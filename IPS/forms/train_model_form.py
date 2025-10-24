import db
import random
import worker_threads as worker
import forms.gui_utils as gui
import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QCloseEvent
from system import system_instance

#this form shows info for training models
class TrainModelConfigForm(QWidget):

    #build the form
    def __init__(self,prepare_save_callback):
        super().__init__()

        #keep reference to training display
        self.training_display= system_instance.display 
        self.save_callback = prepare_save_callback

        
        

        self.setWindowTitle("Training Config")
        self.setMinimumSize(600, 200)
        self.adjustSize()
        self.main_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        
        # Model name text box
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("Enter model name")
        self.form_layout.addRow("Model name:", self.model_name_edit)
        
        # Base models hardcoded
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.model_combo.setMaxVisibleItems(10)

    
   
        # Retrieve models already made
        self.model_combo.addItems(db.get_all_model_names())
        self.form_layout.addRow("Base model:", self.model_combo)
        
        # Extra params area
        self.add_param_btn = QPushButton("Add Parameter")
        self.add_param_btn.clicked.connect(self.add_extra_param)
        self.extra_params_layout = QVBoxLayout()
        self.extra_fields = []  # list of tuples: (param_name_combo, value_widget, layout_container)
        
        # Submit button
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.handle_submit)
        
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.add_param_btn)
        self.main_layout.addLayout(self.extra_params_layout)
        self.main_layout.addWidget(self.submit_btn)
        self.setLayout(self.main_layout)
        
        # List of allowed extra parameters (name + type)
        # Type could be 'int', 'float', 'bool', or maybe string
        self.allowed_params = {
            "amp": "bool",
            "batch": "int or float",
            "box": "float",
            "cache": "bool",
            "classes": "list[int]",
            "close_mosaic": "int",
            "cls": "float",
            "compile": "bool or str",
            "cos_lr": "bool",
            "deterministic": "bool",
            "dfl": "float",
            "dropout": "float",
            "epochs": "int",
            "fraction": "float",
            "freeze": "int or list",
            "imgsz": "int",
            "kobj": "float",
            "lr0": "float",
            "lrf": "float",
            "mask_ratio": "int",
            "momentum": "float",
            "multi_scale": "bool",
            "nbs": "int",
            "optimizer": "str",
            "overlap_mask": "bool",
            "patience": "int",
            "plots": "bool",
            "pose": "float",
            "profile": "bool",
            "rect": "bool",
            "resume": "bool",
            "save_period": "int",
            "seed": "int",
            "single_cls": "bool",
            "time": "float",
            "val": "bool",
            "warmup_bias_lr": "float",
            "warmup_epochs": "float",
            "warmup_momentum": "float",
            "weight_decay": "float",
        }

            
    #add extra configs to form    
    def add_extra_param(self):
        # Create row
        h_layout = QHBoxLayout()

        # Param name combo
        param_name_combo = QComboBox()
        param_name_combo.setEditable(True)
        param_name_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        param_name_combo.setMaxVisibleItems(10)
        param_name_combo.addItems(self.allowed_params.keys())

        h_layout.addWidget(QLabel("Param:"))
        h_layout.addWidget(param_name_combo)

        # Use a list container to hold the value widget so it can be replaced later
        value_widget_container = [QLineEdit()]
        value_widget_container[0].setPlaceholderText("Value")

        h_layout.addWidget(QLabel("Value:"))
        h_layout.addWidget(value_widget_container[0])

        # Pass container to on_param_change so it can replace widget properly
        self.on_param_change(value_widget_container, param_name_combo, h_layout)

        self.adjustSize()

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.handle_remove(param_name_combo, value_widget_container, h_layout, remove_btn))
        h_layout.addWidget(remove_btn)

        param_name_combo.currentIndexChanged.connect(lambda: self.on_param_change(value_widget_container, param_name_combo, h_layout))

        self.extra_params_layout.addLayout(h_layout)
        self.extra_fields.append((param_name_combo, value_widget_container, h_layout))

    #remove a config from the form
    def handle_remove(self, param_name_combo, value_widget_container, h_layout, remove_btn):
        # Remove widgets properly
        for w in (param_name_combo, value_widget_container[0], remove_btn):
            h_layout.removeWidget(w)
            w.hide()
            w.deleteLater()
        self.extra_params_layout.removeItem(h_layout)
        self.extra_fields = [t for t in self.extra_fields if t[2] is not h_layout]

    #handles a config container changing type
    def on_param_change(self, value_widget_container, param_name_combo, h_layout):
        old_widget = value_widget_container[0]
        name = param_name_combo.currentText()
        ptype = self.allowed_params.get(name, "str")

        h_layout.removeWidget(old_widget)
        old_widget.hide()
        old_widget.deleteLater()

        if ptype == "int":
            new_widget = QSpinBox()
            new_widget.setMinimum(-1000000)
            new_widget.setMaximum(1000000)
            new_widget.setValue(0)
        elif ptype == "float":
            new_widget = QDoubleSpinBox()
            new_widget.setDecimals(6)
            new_widget.setMinimum(0.0)
            new_widget.setMaximum(1000000.0)
            new_widget.setValue(0.0)
        elif ptype == "bool":
            new_widget = QComboBox()
            new_widget.addItems(["False", "True"])
        else:  # str
            new_widget = QLineEdit()
            new_widget.setPlaceholderText("Value")

        value_widget_container[0] = new_widget  
        h_layout.insertWidget(3, new_widget)
        new_widget.show()

    #handles submit and training of models
    def handle_submit(self):
        config = {}

        base_model = self.model_combo.currentText()
        config["model"] = base_model

        name = self.model_name_edit.text()
        if name == "":
            gui.show_alert(QMessageBox.Icon.Warning, "Naming Error", "", "Please Enter a name")
            return

        if db.model_name_exists(name):
            gui.show_alert(QMessageBox.Icon.Warning, "Naming Error", "", "Model name is taken")
            return

        config["name"] = name
        try:
            # Extra params
            for (param_name_combo, value_widget_container, _) in self.extra_fields:
                key = param_name_combo.currentText()
                value_widget = value_widget_container[0]  # unwrap the widget from container

                # read the value based on widget type
                if isinstance(value_widget, QSpinBox):
                    val = value_widget.value()
                elif isinstance(value_widget, QDoubleSpinBox):
                    val = value_widget.value()
                elif isinstance(value_widget, QComboBox):
                    # for bools etc
                    val_text = value_widget.currentText()
                    # if bool type, convert
                    if key in self.allowed_params and self.allowed_params[key] == "bool":
                        val = True if val_text == "True" else False
                    else:
                        val = val_text
                else:  # line edit
                    val = value_widget.text()

                config[key] = val

            #generate random seed if one hasint been provided 
            seed = config.get("seed",0)
            if seed == 0:
                seed = random.randint(0, 2**32 - 1)  
                random.seed(seed)                    
                config["seed"] = seed    

            valid, msg = self.validate_config(config)

            if not valid:
                gui.show_alert(QMessageBox.Icon.Warning, "Config Error", "",msg)
                return


            self.worker = worker.ModelTrainerWorker(config)
            

            #call backs for updating user
            self.worker.training_started.connect(self.training_display.add_status_message)
            self.worker.epoch_completed.connect(self.training_display.add_epoch_metrics)
            self.worker.training_finished.connect(self.training_display.add_completion_message)
            self.worker.error_occurred.connect(self.training_display.add_error_message)
            self.worker.status_update.connect(self.training_display.add_status_message)
        
            #call backs for ending TrainModelConfigForm Instance
            self.worker.training_finished.connect(self.handle_worker_completion)
            self.worker.error_occurred.connect(self.handle_worker_error)
            self.worker.prepare_save.connect(self.save_callback)

            #start the worker
            self.worker.start()
            self.hide()
        
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            gui.show_alert(QMessageBox.Icon.Warning, "Training Error", "", "An error occoured while the model was training")

    #validates the config/form
    def validate_config(self,config):
        errors = []
        
        
        # Check for unentered values 
        empty_keys = []
        for key, value in config.items():
            if isinstance(value, str) and value.strip() == "":
                empty_keys.append(key)
            elif isinstance(value,int) and value == 0:
                empty_keys.append(key)
            elif isinstance(value,float) and value == 0.0:
                empty_keys.append(key)
                        

        for key, value in config.items():
            if value is None:
                empty_keys.append(key)

        if empty_keys:
            errors.append(f"Found empty values for keys: {', '.join(empty_keys)}")


        # Return validation result
        if errors:
            error_message = ". ".join(errors)
            return False, error_message
        
        return True, "Configuration is valid"

    def handle_worker_completion(self):
        self.close()

    def handle_worker_error(self):
        self.close()
        
    def closeEvent(self, event: QCloseEvent):

        system_instance.process_going = False
        
        event.accept()