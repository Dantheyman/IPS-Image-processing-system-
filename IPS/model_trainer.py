import os
import shutil
import db
from config import WORKING_DIR
from ultralytics import YOLO


def complete_config(config):
    
    runs_path = os.path.join(WORKING_DIR,"runs")
    if os.path.exists(runs_path):
        shutil.rmtree(runs_path)

    data_path = os.path.join(WORKING_DIR,"data.yaml")
    
    os.mkdir(runs_path)
    config["project"] = runs_path
    config["verbose"] = False
    config["data"] = data_path
    config["model"] = db.get_model_path(config["model"])
    return config

def train_model(config,worker_thread):
        try:
            # Suppress YOLO verbose output
            os.environ['YOLO_VERBOSE'] = 'False'
            

            
           
            worker_thread.status_update.emit("Loading model...")

            model = config.pop("model")
            model = YOLO(model)
            
            # Add callbacks for monitoring
            model.add_callback('on_train_start', worker_thread.on_train_start)
            model.add_callback('on_train_epoch_end', worker_thread.on_train_epoch_end)
            model.add_callback('on_train_end', worker_thread.on_train_end)
            
            worker_thread.status_update.emit("Starting training...")
            
            return model.train(**config)
                
        
        except Exception as e:
            worker_thread.error_occurred.emit(f"Training failed: {str(e)}")