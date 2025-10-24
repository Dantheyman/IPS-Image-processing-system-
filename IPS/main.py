
import sys
import db
import forms.gui_utils as gui
from PyQt6 import QtWidgets
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from forms.create_dataset_form import DatasetCreatorForm
from forms.load_dataset_form import DatasetLoaderForm
from forms.train_model_form import TrainModelConfigForm
from forms.validate_model_form import ValidateModelForm
from system import system_instance
from forms.progress import TrainingMetricsDisplay, DatasetStatusDisplay, ValidateMetricDisplay



data_list=[]


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # load pyqt6 gui base file
        uic.loadUi("forms/ips_main_gui.ui", self)

        #reference to stop pop ups being garbage collected
        self.popup_ref =None

        self.process_going = False
    
        self.create_dataset_button.clicked.connect(self.create_dataset)
        self.load_dataset_button.clicked.connect(self.load_dataset)
        self.train_model_button.clicked.connect(self.train_model)
        self.save_model_button.clicked.connect(self.save_model)
        self.validate_model_button.clicked.connect(self.validate_model)
        


        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.save_model_button.hide()


    def create_dataset(self):

        if system_instance.process_going:
            return


        system_instance.process_going = True
        system_instance.display= DatasetStatusDisplay(self.listWidget, self.label)
        system_instance.display.clear_display()
        self.popup_ref = DatasetCreatorForm()
        self.popup_ref.show()
        

    def load_dataset(self):


        if system_instance.process_going:
            return


        system_instance.process_going = True
        system_instance.display = DatasetStatusDisplay(self.listWidget, self.label)
        system_instance.display.clear_display()
        self.popup_ref = DatasetLoaderForm()
        self.popup_ref.show()

    def train_model(self):

        
        if system_instance.process_going:
            return



        if system_instance.loaded_dataset == None:
            gui.show_alert(QMessageBox.Icon.Warning, "No Model Loaded", "", "Please Create or Load a Dataset")
            return
        
        system_instance.process_going = True
        system_instance.display = TrainingMetricsDisplay(self.listWidget, self.label)
        system_instance.display.clear_display()
        self.popup_ref = TrainModelConfigForm(self.prepare_save)
        self.popup_ref.show()
 
    def validate_model(self):
        if system_instance.process_going:
            return
        system_instance.process_going = True
        system_instance.display = ValidateMetricDisplay(self.listWidget, self.label)
        system_instance.display.clear_display()
        self.popup_ref = ValidateModelForm()
        self.popup_ref.show()

    def save_model(self):
        db.save_model(self.results_doc)

    def prepare_save(self,results_doc):
        self.save_model_button.show()

        self.results_doc = results_doc

     
    

# run the application
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
