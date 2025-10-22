from PyQt6.QtWidgets import   QListWidgetItem 
from PyQt6.QtCore import  pyqtSignal, QObject
from PyQt6.QtGui import QColor






class DatasetStatusDisplay(QObject):

    finished = pyqtSignal()


    def __init__(self, list_widget, status_label=None, parent=None):
        super().__init__(parent)
        self.list_widget = list_widget
        self.status_label = status_label

    def clear_display(self):
        """Clear the metrics display"""
        self.list_widget.clear()

    def update_progress(self, status_text, complete):
    
    
        if complete:
            self.add_status_message(status_text,colour="green")
            self.finished.emit()
        else:
            self.add_status_message(status_text)

    def add_status_message(self, message, colour=None):
    
        
        item = QListWidgetItem(message)        
        self.list_widget.addItem(item)
        if colour:
            item.setForeground(QColor(colour))
        
        # Auto-scroll to bottom
        self.list_widget.scrollToBottom()
    
        
class ValidateMetricDisplay:
        def __init__(self, list_widget, status_label=None):
            self.list_widget = list_widget
            self.status_label = status_label
        
        
        def clear_display(self):
            """Clear the metrics display"""
            self.list_widget.clear()

        def add_status_message(self, message, colour=None):
    
        
            item = QListWidgetItem(message)        
            self.list_widget.addItem(item)
            if colour:
                item.setForeground(QColor(colour))
            
            # Auto-scroll to bottom
            self.list_widget.scrollToBottom()

        def add_completion_message(self, results):
            """Add validation completion message"""

            
            message = (f"Validation completed! Precision: {results['precision']:.3f}, "
                        f"Recall: {results['recall']}, mAP50: {results['mAP50']}, "
                        f"mAP50_95: {results['mAP50_95']}")
            self.add_status_message(message, "blue")
        

class TrainingMetricsDisplay:


    """Helper class to manage metrics display in QListWidget"""
    
    def __init__(self, list_widget, status_label=None):
        self.list_widget = list_widget
        self.status_label = status_label
        
    def clear_display(self):
        """Clear the metrics display"""
        self.list_widget.clear()
        
    def add_status_message(self, message, colour=None):
    
        
        item = QListWidgetItem(message)        
        self.list_widget.addItem(item)
        if colour:
            item.setForeground(QColor(colour))
        
        # Auto-scroll to bottom
        self.list_widget.scrollToBottom()


    def add_epoch_metrics(self, metrics):
        """Add epoch metrics to the display"""
        epoch = metrics['epoch']
        total = metrics['total_epochs']
        mAP50 = metrics['mAP50']
        mAP50_95 = metrics['mAP50_95']
        precision = metrics['precision']
        recall = metrics['recall']
        fitness = metrics['fitness']
        elapsed = metrics['elapsed_time']
        progress = metrics['progress_percent']
        is_best = metrics['is_best']
        
        # Format the metrics message
        metrics_text = (f"Epoch {epoch}/{total} ({progress:.1f}%) - "
                       f"mAP50: {mAP50:.3f}, mAP50-95: {mAP50_95:.3f}, "
                       f"Precision: {precision:.3f}, Recall: {recall:.3f}, "
                       f"Fitness: {fitness}, Time: {elapsed}")
        
        # Add best indicator
        if is_best:
            metrics_text += " NEW BEST!"
            colour = "green"
        else:
            colour = None
        
        self.add_status_message(metrics_text, colour = colour)
    
    def add_error_message(self, error):
        """Add error message to display"""
        self.add_status_message(f"ERROR: {error}", colour ="red")
    
    def add_completion_message(self, results):
        """Add training completion message"""
        if results['success']:
            message = (f"Training completed! Best Fitness: {results['best_fitness']:.3f}, "
                      f"Total time: {results['total_time']}")
            self.add_status_message(message, "blue")

            results_to_save = {}
            results_to_save['success'] = results['success']
            results_to_save['best_epoch'] = results.get('best_epoch')
            results_to_save['mAP50'] = results.get('best_mAP50')
            results_to_save['mAP50_95'] = results.get('best_mAP50-95')
            results_to_save['precision'] = results.get('precision')
            results_to_save['recall'] = results.get('recall')
            results_to_save['fitness'] = results.get('fitness')


        else:
            self.add_status_message("Training failed!", colour = "red")
            
