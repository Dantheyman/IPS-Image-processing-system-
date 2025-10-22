import db
import worker_threads as worker
import forms.gui_utils as gui
import traceback
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QSizePolicy,QSpacerItem, QVBoxLayout,
    QComboBox,  QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QCloseEvent
from system import system_instance

class ValidateModelForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model Validator Form")

        #keep reference to training display
        self.display= system_instance.display  

        self.search_type_inputs = [] 

        dataset_names = db.get_all_dataset_names()
        model_names = db.get_all_model_names()

        # Dataset name input
        self.dataset_name_input = QComboBox()
        #let user type but not add values to the combo box
        self.dataset_name_input.setEditable(True)
        self.dataset_name_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.dataset_name_input.addItems(dataset_names)


        #Model name input
        self.model_name_input = QComboBox()
        #let user type but not add values to the combo box
        self.model_name_input.setEditable(True)
        self.model_name_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.model_name_input.addItems(model_names)

        self.validate_model_layout = QFormLayout()
        self.validate_model_layout.addRow("Model Name:",self.model_name_input)
        self.validate_model_layout.addRow("Dataset Name:", self.dataset_name_input)


        # Bottom buttons: Cancel and load
        self.cancel_btn = QPushButton("Cancel")
        self.validate_btn = QPushButton("Validate")

        bottom_buttons = QHBoxLayout()
        bottom_buttons.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        bottom_buttons.addWidget(self.cancel_btn)
        bottom_buttons.addWidget(self.validate_btn)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.validate_model_layout) 
        main_layout.addLayout(bottom_buttons)
        self.setLayout(main_layout)

        # Connect signals
        self.cancel_btn.clicked.connect(self.on_cancel)
        self.validate_btn.clicked.connect(self.on_validate)

        
    


            
            
    def on_validate(self):
        try:

            self.worker = worker.ModelValidatorWorker(self.model_name_input.currentText(),self.dataset_name_input.currentText())

            #call backs for updating users)
            self.worker.status_update.connect(self.display.add_status_message)
            self.worker.validation_finished.connect(self.display.add_completion_message)
           
        
            #call backs for ending TrainModelConfigForm Instance
            self.worker.validation_finished.connect(self.handle_worker_completion)
            self.worker.error_occurred.connect(self.handle_worker_error)

            #start the worker
            self.worker.start()
            self.hide()
        
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            gui.show_alert(QMessageBox.Icon.Warning, "Validation Error", "", "An error occoured while validating the model")


    def handle_worker_completion(self):
        self.close()

    def handle_worker_error(self):
        self.close()
        
    def on_cancel(self):
        self.close()

    def closeEvent(self, event: QCloseEvent):

        system_instance.process_going = False
        
        event.accept()