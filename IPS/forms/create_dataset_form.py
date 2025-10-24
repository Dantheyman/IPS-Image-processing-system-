import forms.gui_utils as gui_utils
import db
import worker_threads as worker
from system import system_instance
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel,
    QHBoxLayout, QVBoxLayout, QFormLayout, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QCloseEvent

# This Class is responsible for handling the form popup for creation of a dataset
class DatasetCreatorForm(QWidget):

    #build the form
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Search Form")


        #in future this should be defined somehow by user, for now it is hardcoded 
        self.classes  = "tree"


       
        self.search_type_inputs = [] 

        
        # Dataset name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Dataset Name")
        self.name_layout = QFormLayout()
        self.name_layout.addRow("Dataset Name:", self.name_input)


        # Top buttons to add fields
        self.add_exact_btn = QPushButton("Add Exact")
        self.add_range_btn = QPushButton("Add Range")

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.add_exact_btn)
        top_buttons.addWidget(self.add_range_btn)

        # Form layout for fields
        self.form_layout = QFormLayout()
        self.form_area = QWidget()
        self.form_area.setLayout(self.form_layout)

        # Bottom buttons: Cancel and Create
        self.cancel_btn = QPushButton("Cancel")
        self.create_btn = QPushButton("Create")

        bottom_buttons = QHBoxLayout()
        bottom_buttons.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        bottom_buttons.addWidget(self.cancel_btn)
        bottom_buttons.addWidget(self.create_btn)

        # Row for Train/Test/Val splits
        split_layout = QHBoxLayout()
        split_form_layout = QFormLayout()

        self.train_input = QLineEdit()
        self.train_input.setPlaceholderText("Train %")

        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("Test %")

        self.val_input = QLineEdit()
        self.val_input.setPlaceholderText("Validation %")

        # Add labels + textboxes inline
        split_layout.addWidget(QLabel("Train"))
        split_layout.addWidget(self.train_input)
        split_layout.addWidget(QLabel("Test"))
        split_layout.addWidget(self.test_input)
        split_layout.addWidget(QLabel("Val"))
        split_layout.addWidget(self.val_input)
        split_form_layout.addRow("Dataset Split:", split_layout)
    
        

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.name_input)
        main_layout.addLayout(top_buttons)
        main_layout.addWidget(self.form_area)
        main_layout.addLayout(split_form_layout)
        main_layout.addLayout(bottom_buttons)
        
        self.setLayout(main_layout)

        # Connect signals
        self.add_exact_btn.clicked.connect(self.add_exact_field)
        self.add_range_btn.clicked.connect(self.add_range_field)
        self.cancel_btn.clicked.connect(self.on_cancel)
        self.create_btn.clicked.connect(self.on_create)

    # adds a exact search to the form 
    def add_exact_field(self):
        # Field 
        field_input = QLineEdit()
        field_input.setPlaceholderText("Field")
        self.search_type_inputs.append(field_input)

        # Single value input
        value_input = QLineEdit()
        value_input.setPlaceholderText("Value")

        remove_button = QPushButton("❌")

        row_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field_input)
        layout.addWidget(value_input)
        layout.addWidget(remove_button)
        row_widget.setLayout(layout)

        self.form_layout.addRow("", row_widget)

        remove_button.clicked.connect(lambda _, w=row_widget: self.remove_row(w))


        self.sync_search_input_widths()

    # Adds a range search to the form
    def add_range_field(self):
        # Search Type input (text)
        field_input = QLineEdit()
        field_input.setPlaceholderText("Field")
        self.search_type_inputs.append(field_input)

        # Two value inputs: Min and Max
        min_input = QLineEdit()
        min_input.setPlaceholderText("Min")
        max_input = QLineEdit()
        max_input.setPlaceholderText("Max")

        remove_button = QPushButton("❌")

        row_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field_input)
        layout.addWidget(min_input)
        layout.addWidget(QLabel("–"))
        layout.addWidget(max_input)
        layout.addWidget(remove_button)
        row_widget.setLayout(layout)

        self.form_layout.addRow("", row_widget)

        remove_button.clicked.connect(lambda _, w=row_widget: self.remove_row(w))


        self.sync_search_input_widths()

    # removes a row from form 
    def remove_row(self, widget):
        for i in range(self.form_layout.rowCount()):
            field_widget = self.form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if field_widget == widget:
                # Remove corresponding search_type_input
                search_inputs_in_row = field_widget.findChildren(QLineEdit)
                if search_inputs_in_row:
                    search_type_input = search_inputs_in_row[0]
                    if search_type_input in self.search_type_inputs:
                        self.search_type_inputs.remove(search_type_input)

                self.form_layout.removeRow(i)
                
                break

        self.sync_search_input_widths()

    # keeps the left most textbox the same size, making form look better
    def sync_search_input_widths(self):
        if not self.search_type_inputs:
            return

        max_width = max(input.sizeHint().width() for input in self.search_type_inputs)
        for input in self.search_type_inputs:
            input.setFixedWidth(max_width)

    # closes the form when cancel button is hit 
    def on_cancel(self):
        self.close()

    # when the create button is clicked, create a dataset
    def on_create(self):
        # Gather form input values
        form_data = {"exact": {}, "range": {}}
        
        for i in range(self.form_layout.rowCount()):
            row_widget = self.form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if not row_widget:
                continue

            inputs = row_widget.findChildren(QLineEdit)
            if len(inputs) == 2:  # Exact match
                key, value = inputs[0].text().strip(), inputs[1].text().strip()
                form_data["exact"][key] = value
            elif len(inputs) == 3:  # Range match
                key = inputs[0].text().strip()
                start = inputs[1].text().strip()
                end = inputs[2].text().strip()
                form_data["range"][key] = f"{start},{end}"

        # Validate form input data
        valid, message = self.validate_form_data(form_data)
        if not valid:
            gui_utils.show_alert(QMessageBox.Icon.Warning, "Validation Error", "", message)
            return

        # Validate split values (train/test/val)
        split_inputs = [self.train_input, self.test_input, self.val_input]
        valid, message = self.validate_train_test_val_split(split_inputs)
        if not valid:
            gui_utils.show_alert(QMessageBox.Icon.Warning, "Validation Error", "", message)
            return

        # Validate dataset name
        dataset_name = self.name_input.text().strip()
        if not dataset_name:
            gui_utils.show_alert(QMessageBox.Icon.Warning, "Validation Error", "", "Dataset Name is Empty")
            return
        if not db.validate_dataset_name(dataset_name):
            gui_utils.show_alert(QMessageBox.Icon.Warning, "Naming Error", "", "Dataset Name is Taken")
            return

        # Prepare split string and start worker
        
        train = int(self.train_input.text().strip())
        test = int(self.test_input.text().strip())
        val = int(self.val_input.text().strip())
        split_string = f"{train}/{test}/{val}"

        # Show progress window
  
        display = system_instance.display
        display.update_progress("Creating Dataset:", False)
        display.finished.connect(self.handle_worker_completion)

        # Start background worker
        self.worker = worker.DatasetWorker(dataset_name,form_data=form_data,split=split_string, classes= self.classes)
        self.worker.progress.connect(display.update_progress)
        self.worker.error.connect(self.handle_worker_error)
        self.worker.start()
        self.hide()


    #displays error if a unhandled exception happens in a worker thread
    def handle_worker_error(self,e):
        gui_utils.show_alert(QMessageBox.Icon.Warning, "Dataset Creation Error", "", f"{e}")
        self.show()  

    #closes the form completely when the worker thread completes successfully
    def handle_worker_completion(self):
        self.close()

    # validates form to make sure that no simple mistakes such as empty values
    def validate_form_data(self,data):
        message = ""
        exact_dict = data["exact"]
        range_dict = data["range"]
        
        #check there are no empty text boxes
        for field, values in exact_dict.items():
            if (field == "") or (values == ""):
                message = message + "You have an incomplete form\n"
                break
        for field , values in range_dict.items():
            if (field == "") or (values.split[","][0] == "") or (values.split[","][1] == ""):
                message = message + "You have an incomplete form\n"
                break
        seen = set()
        #check there are no conflicting/double up fields 
        for field in exact_dict.keys():
            if field in seen:
                message = message + "You have duplicate fields\n"
                break
            seen.add(field)
        for field in range_dict.keys():
            if field in seen:
                message = message + "You have duplicate fields\n"
                break
            seen.add(field)
    
        if message == "":
            return (True, message)
        else:
            return (False, message)

    #confirms that a given train/test/val split sums to 100%
    def validate_train_test_val_split(self,data):
        message = ""

        test = data[0].text() 
        train = data[1].text()
        val = data[2].text()

        if train == "" or test == "" or val =="":
            message = "All Values for the Train-Test-Val-Split Must be Entered"
            return False,message

        try: 
            test = int(test)
            train = int(train)
            val = int(val)
        except:
            message = "The Train-Test-Val-Split Must be only Numbers"
            return False,message

        percentage = test+train+val

        if percentage == 100:
            return True,message
        
        return False, "Percentages must add to 100"
    
    #indicates to the system that the process is complete 
    def closeEvent(self, event: QCloseEvent):

        system_instance.process_going = False
        
        event.accept()