from PyQt6.QtWidgets import QMessageBox   


def show_alert(icon,window_title,text,informative_text,callback = None):
        msg = QMessageBox()
        msg.setIcon(icon)   # Information, Warning, Critical, Question
        msg.setWindowTitle(window_title)
        msg.setText(text)
        msg.setInformativeText(informative_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        #connect call back to form calling this method
        if callback:
            msg.buttonClicked.connect(lambda btn: callback())

        #show alert and return reference to prevent garbage collection 
        msg.exec()
        return msg   