import os
import sys
import torch
from ultralytics import YOLO
import cv2
import numpy as np
from system import system_instance
import db 
import time


  

# SAM2 Model Setup
def setup_sam2_model(model_cfg="sam2_hiera_b+",checkpoint="checkpoints/sam2_hiera_base_plus.pt"):

    from sam2.build_sam import build_sam2
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Build SAM2 model - use config name without .yaml extension
    sam2_model = build_sam2(model_cfg, checkpoint, device=device)
    
    # Enable half precision for memory efficiency
    sam2_model.half()
        
    return sam2_model

# SAM2 Mask Generator 
def create_sam2_mask_generator(sam2_model):
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    return SAM2AutomaticMaskGenerator(
        model=sam2_model,
        points_per_side=32,
        pred_iou_thresh=0.85,
        stability_score_thresh=0.8,
        crop_n_layers=0,  # Keep 0 for memory efficiency
        crop_overlap_ratio=0.3,
        min_mask_region_area=350,
        points_per_batch=32,
        crop_n_points_downscale_factor=2,
        box_nms_thresh=0.7,
    )

# shrink image to make processing faster
def preprocess_image(image_rgb, target_size=1024):
    height, width = image_rgb.shape[:2]
    
    if max(height, width) > target_size:
        scale = target_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image_rgb

# decrease number of masks as unlikely to be that many trees thus resulting in less processing needed to determine if mask is a tree
def filter_masks(masks, min_area=500, max_masks=10):
    sorted_masks = sorted(masks, key=lambda x: x['area'] * x['stability_score'], reverse=True)
    filtered_masks = [mask for mask in sorted_masks if mask['area'] >= min_area][:max_masks]
    return filtered_masks


# converts a given mask into a yolo annotation 
def convert_masks_to_yolo_annotations(masks, image_shape, class_id=0):
    h_img, w_img = image_shape[:2]
    yolo_annotations = []

    for mask in masks:
        # Get bounding box (x_min, y_min, width, height)
        x_min, y_min, width, height = mask['bbox']
        
        # Convert to YOLO format (normalized center x/y, width, height)
        x_center = (x_min + width / 2) / w_img #Optional: View model architecture/info
        y_center = (y_min + height / 2) / h_img
        w_norm = width / w_img
        h_norm = height / h_img

        # Assign class ID (e.g., 0 for “tree”)
        yolo_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
    
    return yolo_annotations


#saves annotations  to the database 
def save_annotations(annotation, image_path,classes):
    
    # Extract ID 
    photo_id = os.path.splitext(os.path.basename(image_path))[0]

    db.upload_annotations(photo_id,classes,annotation)
   

#determines if image contains a tree
def is_tree(image):

    ################# replace with api request once model deployment is complete ##########
    model_paths = ["checkpoints/best_vX.pt","checkpoints/best_vM.pt","checkpoints/best_vL.pt","checkpoints/best_vS.pt"]
    conf_thresh = 0.4
    agreement_threshold = 0.25


    votes = 0
    total_models = len(model_paths)
    
    for model_path in model_paths:
        model = YOLO(model_path)
        model.eval()
        model.to('cuda')
        results = model(image, verbose=False)
        
        detected = False
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls]
                
                if class_name.lower() == "tree" and conf >= conf_thresh:
                    detected = True
                    break
            if detected:
                break
        
        if detected:
            votes += 1
        del model
    
    agreement_ratio = votes / total_models
    
    
    return agreement_ratio >= agreement_threshold


#extracts only the masked region so that isTree is only looking at that region
# image: numpy array (H, W, C)
# mask: binary mask (H, W) 
def extract_masked_region(image, mask):



    # Ensure mask is boolean
    mask = mask.astype(bool)

    # Apply mask
    masked_image = np.zeros_like(image)
    masked_image[mask] = image[mask]

    # Find bounding box of mask
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return None  # empty mask
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()

    # Crop to bounding box
    cropped = masked_image[y_min:y_max+1, x_min:x_max+1]

    return cropped


def download_dataset_photos(datset_id):
    return db.load_dataset_photos(datset_id)


#retrieves all paths of images from within the dataset
def get_image_paths(dataset_path):
    image_dir = os.path.join(dataset_path, "images")
    subsets = ['train', 'val', 'test']
    extensions = ('.jpg', '.jpeg', '.png', '.bmp')

    all_paths = []

    for subset in subsets:
        subset_dir = os.path.join(image_dir, subset)
        
        for root, dirs, files in os.walk(subset_dir):
            for file in files:
                if file.lower().endswith(extensions):
                    full_path = os.path.abspath(os.path.join(root, file))
                    all_paths.append(full_path)
        
        

    return all_paths

def filter_image_paths(image_paths,classes):
    filtered_paths = []
    for path in image_paths:
        photo_id = os.path.basename(path).split(".")[0]

        annotations = db.get_annotations(photo_id)
    
        add_back = True
        for annotation in annotations:
            annotation_classes = annotation["classes"]
            if set(annotation_classes) == set(classes):
                add_back = False
                break
        if add_back:
            filtered_paths.append(path)
    return filtered_paths



def annotate_dataset(dataset_id, progress_callback):
    start = time.time()


    # put photos into WORKING_DIR
    progress_callback("Downloading Photos",False)
    dataset_path = db.load_dataset_photos(dataset_id)

    classes = db.get_classes(dataset_id)

    # Get image paths dict 
    image_paths = get_image_paths(dataset_path)



    #filter out images that already have annotations for given classes
    image_paths = filter_image_paths(image_paths,classes)
   

    #  Setup SAM2 and generate masks for ALL images
    sam2_model = setup_sam2_model()
    mask_generator = create_sam2_mask_generator(sam2_model)

    # Store all masks per image
    all_masks = {}

    progress_callback("Generating Annotations", False)

    for  image_path in image_paths:
        
        torch.cuda.empty_cache()

        print(f"Processing (SAM2 mask gen) {image_path}")

        # Load & preprocess image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image {image_path}")
            continue

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        original_shape = image_rgb.shape[:2]
        image_rgb = preprocess_image(image_rgb, target_size=1024)
       

        # Generate masks with autocast for fp16
        with torch.amp.autocast(device_type='cuda', dtype=torch.float16):
            masks = mask_generator.generate(image_rgb)


        # Filter masks 
        masks = filter_masks(masks, min_area=300, max_masks=15)
    

        # Save masks info for later
        all_masks[image_path] = {
            "masks": masks,
            "image_rgb": image_rgb  # store preprocessed RGB for later use
        }

    # Clear SAM2 model & free memory
    del sam2_model
    del mask_generator
    torch.cuda.empty_cache()

    # Load YOLOv5 model ONCE ---  want to get rid of this in the future
    yolov5_path = '/home/dj66/Documents/Honours/IPS-Image-processing-system-/IPS/yolov5'
    if yolov5_path not in sys.path:
        sys.path.insert(0, yolov5_path)

 

    # --- PART 3: For each image and its masks, check tree presence and save annotations ---
    progress_callback("Filtering Annotations", False)
    for image_path, data in all_masks.items():
        image_rgb = data["image_rgb"]
        masks = data["masks"]

        tree_masks = []

   

        for mask in masks:
            cropped_image = extract_masked_region(image_rgb, mask['segmentation'])
            if cropped_image is None or cropped_image.size == 0:
                continue

            # Check if mask region contains a tree
            if is_tree(cropped_image):
                tree_masks.append(mask)
                torch.cuda.empty_cache()

        annotations = convert_masks_to_yolo_annotations(tree_masks, image_rgb.shape)

        if annotations:
            save_annotations(annotations, image_path, classes)
            print(f"Saved annotations for {image_path}")
        else:
            print(f"No tree annotations found for {image_path}")
            os.remove(image_path)
            photo_id = image_path.split("/")[-1].split(".")[0]
            db.remove_photo_from_dataset(dataset_id,photo_id)

    # Clean up YOLOv5 model & memory
    torch.cuda.empty_cache()

    end = time.time()
    print(f"Elapsed time: {end - start:.4f} seconds")
    # Notify system of dataset update
    system_instance.change_dataset(dataset_id)



 
