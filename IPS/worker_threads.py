import traceback
from datetime import datetime
import dataset_annotater
import model_trainer
import model_validator
import db
from PyQt6.QtCore import QThread, pyqtSignal
from system import system_instance

class DatasetWorker(QThread):

    progress = pyqtSignal(str,bool)    
    error = pyqtSignal(str)


        
        
  
    def __init__(self, dataset_name, form_data = None, split = None, classes = None):
        super().__init__()
        self.dataset_name = dataset_name
        self.form_data = form_data
        self.split = split
        self.annotating = False
        self.classes = classes

        if form_data is not None and split is not None:

            self.annotating = True

    def run(self):


        try: 
            if self.annotating:
                dataset_id = db.create_dataset(self.dataset_name, self.form_data, self.split, self.classes)
                dataset_annotater.annotate_dataset(dataset_id, progress_callback=self.progress.emit)
                system_instance.change_dataset(dataset_id)
                self.progress.emit("Dataset Creation Complete:",True)
            else:
                dataset_id = db.get_dataset_id(self.dataset_name)
                system_instance.change_dataset(dataset_id)
                self.progress.emit("Dataset Loaded", True)
            
            
        except Exception as e:
            
            tb_str = traceback.format_exc()
            print(tb_str)
            self.error.emit(str(e)) 


class ModelValidatorWorker(QThread):

    validation_finished = pyqtSignal(dict) # send final results
    status_update = pyqtSignal(str)  # Send general status updates 
    error_occurred = pyqtSignal(str)

    def __init__(self,model_name,dataset_name):
        super().__init__()
        self.model_name = model_name
        self.dataset_name = dataset_name 
    
      
    def run(self):
        try:
            model_validator.validate_model(self.model_name,self.dataset_name,self)
        except Exception as e:
            
            tb_str = traceback.format_exc()
            print(tb_str)
            self.error_occurred.emit(str(e)) 
            


    def on_val_start(self,trainer):
        self.status_update.emit("Validation Started")

    def on_val_end(self, trainer):
        metrics = trainer.metrics

        # Ensure metrics are available before accessing them
        if not metrics:
            print("No metrics found.")
            return

        results = {
            "mAP50": metrics.box.map50,
            "mAP50_95": metrics.box.map,
            "recall": metrics.box.mr,
            "precision": metrics.box.mp,
        }

        self.validation_finished.emit(results)


class ModelTrainerWorker(QThread):
    

    # Signals to communicate with main thread
    training_started = pyqtSignal(str)  # Send status message
    epoch_completed = pyqtSignal(dict)  # Send epoch metrics
    training_finished = pyqtSignal(dict)  # Send final results
    error_occurred = pyqtSignal(str)  # Send error messages
    status_update = pyqtSignal(str)  # Send general status updates 
    prepare_save = pyqtSignal(dict) #sends important metadata so its ready to save
    

    def __init__(self,config):
        super().__init__()
        self.config = config  
        self.best_mAP50 = 0
        self.current_epoch = 0 
        self.best_fitness = 0

        
        self.total_epochs = self.config.get("epochs", 0)
        if self.total_epochs == 0:
            self.total_epochs = 100
        


    def run(self):
        try: 

            explicit_config = model_trainer.complete_config(self.config.copy())
            model_trainer.train_model(explicit_config, self)
     
            
        except Exception as e:
            
            tb_str = traceback.format_exc()
            print(tb_str)
            self.error_occurred.emit(str(e)) 


    def on_train_start(self,trainer):
        """Called when training starts"""
        self.start_time = datetime.now()
        self.training_started.emit(f"Training started at {self.start_time.strftime('%H:%M:%S')}")
        self.status_update.emit(f"Training for {self.total_epochs} epochs...")

    def on_train_epoch_end(self, trainer):
        """Called at the end of each epoch"""
        try:
            # Extract metrics from trainer
            metrics = trainer.metrics 
            
            # Get key metrics (handle missing keys gracefully)
            mAP50 = metrics.get('metrics/mAP50(B)', 0)
            mAP50_95 = metrics.get('metrics/mAP50-95(B)', 0)
            precision = metrics.get('metrics/precision(B)', 0)
            recall = metrics.get('metrics/recall(B)', 0)
            box_loss = metrics.get('val/box_loss', 0)
            cls_loss = metrics.get('val/cls_loss', 0)
            fitness = trainer.fitness
            
            # Track best fitness
            if fitness is not None and fitness > self.best_fitness:
                self.best_fitness = fitness
                is_best = True
            else:
                is_best = False
            
            # Calculate elapsed time
            elapsed = datetime.now() - self.start_time if self.start_time else None
            elapsed_str = str(elapsed).split('.')[0] if elapsed else "Unknown"
            self.current_epoch += 1
            # Create metrics dictionary
            epoch_metrics = {
                'best_fitness' : self.best_fitness,
                'epoch': self.current_epoch ,
                'total_epochs': self.total_epochs,
                'mAP50': mAP50,
                'mAP50_95': mAP50_95,
                'precision': precision,
                'recall': recall,
                'fitness':fitness,
                'box_loss': box_loss,
                'cls_loss': cls_loss,
                'is_best': is_best,
                'elapsed_time': elapsed_str,
                'progress_percent': ((self.current_epoch) / self.total_epochs) * 100
            }
            
            # Send metrics to main thread
            self.epoch_completed.emit(epoch_metrics)
            
            
            
        except Exception as e:
            self.error_occurred.emit(f"Error processing epoch metrics: {str(e)}")
    
    def on_train_end(self, trainer):
        """Called when training completes"""
        try:
            total_time = datetime.now() - self.start_time if self.start_time else None
            total_time_str = str(total_time).split('.')[0] if total_time else "Unknown"
            
            # Get final results
            results = {
                'completed_epochs': self.current_epoch,
                'best_fitness': self.best_fitness,
                'total_time': total_time_str,
                'model_path': getattr(trainer, 'save_dir', 'Unknown'),
                'success': True
            }
            #send results to trainingDisplay
            self.training_finished.emit(results)
            
            # Initialize metadata dictionary
            metadata = {}

            # Retrieve metrics from trainer
            metrics = trainer.metrics
            metadata["best_mAP50"] = self.best_mAP50
            metadata['mAP50'] = metrics.get('metrics/mAP50(B)', 0) 
            metadata['AP50_95'] = metrics.get('metrics/mAP50-95(B)', 0)
            metadata['precision'] = metrics.get('metrics/precision(B)', 0)
            metadata['recall'] = metrics.get('metrics/recall(B)', 0)


            doc = {}
            doc["results"] = metadata
            name = self.config.pop("name")
            doc['config'] = self.config
            doc['name'] = name
            doc ['dataset_id'] = system_instance.loaded_dataset.id
            self.prepare_save.emit(doc)

            
            
        except Exception as e:
            self.error_occurred.emit(f"Error in training completion: {str(e)}")







