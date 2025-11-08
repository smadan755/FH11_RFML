from PySide6.QtWidgets import *
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        central_widget = QWidget()
        
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        self.button = QPushButton("Run")
        
        
        
        self.button.clicked.connect(self.click_button)
        
        self.waveform_drop_down = QComboBox()

        
        waveforms = ["PAM", "QAM", "FM"]
        
        for waveform in waveforms:
            self.waveform_drop_down.addItem(waveform)
            
        layout.addWidget(self.waveform_drop_down)
        
        central_widget.setLayout(layout)

        layout.addWidget(self.button)

        
        
    
    def click_button(self):
        print(f"Running: {self.waveform_drop_down.currentText()}!")
        
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())