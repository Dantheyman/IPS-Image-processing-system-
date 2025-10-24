import requests
from config import DATABASE_URL, WORKING_DIR
import os 



######################## Datset Interactions ########################
#confirms with the database that the name provided is free to take
def validate_dataset_name(name):
    params = {"name" : name}
    response = requests.get(DATABASE_URL+"/dataset/name",params = params)
    data = response.json()

    if response.status_code == 200:
        if data.get("name_exists") == True:
            return False
        else:
            return True
    else:
        raise Exception("An error occoured while validating dataset_name")
    
#creates a dataset on the database 
def create_dataset(name,filters,split,classes):
    
    params = {"split": split, "name": name,"classes":classes}

    response = requests.post(DATABASE_URL + "/dataset/photos", params = params, json = filters)

    if response.status_code == 200:
        data = response.json()
        return data.get("id")
    else:
        raise Exception("An error occoured while creating dataset")

#load all dataset photos into working dir
def load_dataset_photos(dataset_id):
    """
    Loads dataset photos into the working directory 

    Args:
       id (string): ID of dataset

    Returns:
        string: Path of folder holding images

    Raises:
        Exception: If eror occours during download 
    """
    
    params = {"dataset_id": dataset_id}
    response = requests.get(DATABASE_URL + "/dataset/photos", params = params, stream=True)

    if response.status_code == 200:
        data = response.json()
      
        return data["path"]

    else:
        print(f"Failed to download. Status code: {response.status_code}")
        raise Exception("Error Downloading Dataset Photos")


#retrieves dataset Id that belongs to name provided
def get_dataset_id(dataset_name):
    params = {"name" : dataset_name }

    response = requests.get(DATABASE_URL+"/dataset/id", params=params)
    
    if response.status_code == 200:
        data = response.json()
     
        return data["id"]
    else: 
        raise Exception("Error Retrieving Dataset ID from Database")   


#retrieves all dataset names in alphabetical order
def get_all_dataset_names():
    
    response = requests.get(DATABASE_URL + "/datasets/names")
    
    if response.status_code == 200:
        data = response.json()
        return data["names"]
    else: 
        raise Exception("Error Retrieving Dataset Names from Database")   


#lets the server know to load dataset into WORKING_DIR
def load_dataset(dataset_id):
    params = {"dataset_id" : dataset_id}
    response = requests.get(DATABASE_URL + "/dataset", params = params, stream=True)

    if response.status_code == 200:
        return

    else:
        print(f"Failed to download. Status code: {response.status_code}")
        raise Exception("Error Downloading Dataset")

def get_classes(dataset_id):
    params = {"dataset_id" : dataset_id}
    response = requests.get(DATABASE_URL + "/dataset/metadata", params = params,)

    if response.status_code == 200:
        data = response.json()
        return data["classes"]

    else:
        print(f"Failed to get dataset classes. Status code: {response.status_code}")
        raise Exception("Error Getting Dataset Classes")

def remove_photo_from_dataset(dataset_id,photo_id):
    params = {
                "dataset_id": dataset_id,
                "photo_id" : photo_id
    }
    response = requests.delete(DATABASE_URL + "/dataset/photo", params = params)

    if response.status_code == 200:
        return

    else:
        print(f"Failed to remove photo from dataset: Status code: {response.status_code}")
        raise Exception("Error Deleting Photo")


######################## Annotation Interactions ########################

#uploads annotations to DMS
#param: photo_id: id of photo being annotated for
#param: classes: list of classes being annotated for 
#param: annotation: String of yolo annotations
def upload_annotations(photo_id,classes,annotation):
    

    data = {
                "photo_id" : photo_id,
                "classes" : classes,
                "annotation" : annotation
            }
    response = requests.post(DATABASE_URL+"/annotations", json=data)
    

    if response.status_code != 200:
        raise Exception("An error occoured uploading annoatations")

#gets a annotation for a given photo
def get_annotations(photo_id):
    params = {"photo_id" : photo_id}
    response = requests.get(DATABASE_URL + "/annotations/photo", params = params)

    if response.status_code == 200:
        data = response.json()
        return data["annotations"]

    else:
        print(f"Failed to get Annotations for photo {photo_id}. Status code: {response.status_code}")
        raise Exception("Error Retriving Annotations")
    


######################## Model Interactions ########################

#gets list of all model metadata
def get_all_models():
    response = requests.get(DATABASE_URL+"/models")

    if response.status_code == 200:
        data = response.json()
        return data["models"]
    else:
        print(f"Failed. Status code: {response.status_code}")
        raise Exception("Error Retrieving Model Data")

#gets a list of all model names
def get_all_model_names():
    models = get_all_models()


    default = []
    homemade = []

    for  model in models:
        if model["base_model"] == True:
            default.append(model["name"])
        else:
            homemade.append(model["name"])

    # Sort both lists alphabetically by name
    default.sort()
    homemade.sort()

    # Combine into one ordered list
    ordered = default + homemade

   
    return ordered

#checks if the model name already exists
def model_name_exists(model_name):
    params = {"model_name": model_name}
    response = requests.get(DATABASE_URL+"/models/name", params = params)

    if response.status_code == 200:
        data = response.json()

        return data["name_exists"]
    else:
        print(f"Failed Status code: {response.status_code}")
        raise Exception("Error Retrieving Model Data")

#gets path to model, assumes DMS and IPS on same machine. 
def get_model_path(model_name):
    
    params = {"model_name": model_name}
    response = requests.get(DATABASE_URL+"/models/path", params = params)

    if response.status_code == 200:
        data = response.json()
        return data["file_path"]
    else:
        print(f"Failed Status code: {response.status_code}")
        raise Exception("Error Retrieving Model Data")

#saves model metadata and weights to DMS
#param: model_doc: dict of model metadata
def save_model(model_doc):

    response = requests.post(DATABASE_URL+"/models",json = model_doc)
    if response.status_code == 200:
        data = response.json()
        model_id = data["id"]

        model_path = os.path.join(WORKING_DIR,"runs",model_doc["name"],"weights","best.pt")
        upload_model(model_id,model_path)

    else:
        print(f"Failed Status code: {response.status_code}")
        raise Exception("Error Retrieving Model Data")

#uploads model weights to DMS
#param: model_id: id of model
#param: model_path: current path of weights to be uploaded
def upload_model(model_id,model_path):
   
    # Open file in binary mode
    with open(model_path, "rb") as f:
        files = {
            "file": (os.path.basename(model_path), f, "application/octet-stream")
        }
        # Additional data if needed
        data = {
            "model_id": model_id
        }

        response = requests.post(f"{DATABASE_URL}/models/path", files=files, data=data)
        if response.status_code != 200:
            print(f"Failed Status code: {response.status_code}")
            raise Exception("Error Saving Model")