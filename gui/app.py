from PySide6.QtWidgets import *
import sys

from main_window import MainWindow
from ml import MLWidget


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_window = MainWindow()
        self.ml_widget = MLWidget()
        
        self.menu = QTabWidget()
        
        self.menu.addTab(self.main_window, "Generate Waveforms")
        self.menu.addTab(self.ml_widget, "Classify Waveforms")
        
        self.setCentralWidget(self.menu)
        self.setWindowTitle("RF ML App")
        self.resize(1200, 800)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

