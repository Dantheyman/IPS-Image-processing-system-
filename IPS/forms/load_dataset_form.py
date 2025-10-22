import db
import forms.gui_utils as gui_utils
import worker_threads as worker
from system import system_instance
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QComboBox,
    QHBoxLayout, QVBoxLayout, QFormLayout, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QCloseEvent

# This Class is responsible for handling the form popup for creation of a dataset
class DatasetLoaderForm(QWidget):

    def __init__(self):
        
        super().__init__()
        self.setWindowTitle("Dataset Search Form")


        self.search_type_inputs = [] 

        names = db.get_all_dataset_names()

        # Dataset name input
        self.name_input = QComboBox()
        self.name_input.setEditable(True)
        self.name_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.name_input.addItems(names)
        self.name_layout = QFormLayout()
        self.name_layout.addRow("Dataset Name:", self.name_input)

        # Bottom buttons: Cancel and load
        self.cancel_btn = QPushButton("Cancel")
        self.load_btn = QPushButton("Load")

        bottom_buttons = QHBoxLayout()
        bottom_buttons.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        bottom_buttons.addWidget(self.cancel_btn)
        bottom_buttons.addWidget(self.load_btn)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.name_input)
        main_layout.addLayout(bottom_buttons)
        self.setLayout(main_layout)

        # Connect signals
        self.cancel_btn.clicked.connect(self.on_cancel)
        self.load_btn.clicked.connect(self.on_load)

    def on_cancel(self):
        self.close()

    def on_load(self):
        dataset_name = self.name_input.currentText()


        #show status to user
        display = system_instance.display
        display.update_progress("Loading Dataset:", False)
        display.finished.connect(self.handle_worker_completion)

        self.worker = worker.DatasetWorker(dataset_name)
        self.worker.progress.connect(display.update_progress)
        self.worker.error.connect(self.handle_worker_error)
        self.worker.start()
        self.hide()
    
    def handle_worker_completion(self):
        self.close()

    def handle_worker_error(self,e):
        gui_utils.show_alert(QMessageBox.Icon.Warning, "Dataset Creation Error", "", f"{e}")  
        self.show()  

    def closeEvent(self, event: QCloseEvent):

        system_instance.process_going = False
        
        event.accept()