import db
from config import WORKING_DIR
from ultralytics import YOLO

def validate_model(model_name, dataset_name, worker_thread):

    worker_thread.status_update.emit("Loading Dataset:")
    dataset_id = db.get_dataset_id(dataset_name)
    db.load_dataset(dataset_id)
    worker_thread.status_update.emit("Dataset Loaded:")


    model_path = db.get_model_path(model_name)
    model = YOLO(model_path)

    model.add_callback('on_val_start', worker_thread.on_val_start)
    model.add_callback('on_val_end', worker_thread.on_val_end)

    
    model.val(data=f"{WORKING_DIR}/data.yaml")

