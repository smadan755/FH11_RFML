from PySide6.QtWidgets import *
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from waveform_functions import *
import matlab.engine
import numpy as np
import matplotlib.pyplot as plt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.eng = matlab.engine.start_matlab()
        
        self.eng.addpath(f"C:\\Users\\madan\\FH11_RFML\\gui\\waveform_functions", nargout=0)

        
        # Create central widget with horizontal layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Add SelectionWidget on the left
        self.selection_widget = SelectionWidget()
        main_layout.addWidget(self.selection_widget)
        
        # Add PlottingWidget on the right
        self.plotting_widget = PlottingWidget()
        main_layout.addWidget(self.plotting_widget)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self.setWindowTitle("RFML Waveform Plotter")
        self.resize(1200, 600)
        
        self.selection_widget.button.clicked.connect(self.click_button)
    
    def click_button(self):
        # Get values from line edits
        waveform = self.selection_widget.waveform_drop_down.currentText()
        fs = float(self.selection_widget.fs_edit.text())
        tsymb = float(self.selection_widget.tsymb_edit.text())
        fc = float(self.selection_widget.fc_edit.text())
        m = float(self.selection_widget.m_edit.text())
        var = float(self.selection_widget.var_edit.text())
        nsymb = int(self.selection_widget.nsymb_edit.text())
        
        print(f"Running: {waveform}")
        print(f"Parameters: fs={fs}, Tsymb={tsymb}, fc={fc}, M={m}, Var={var}, Nsymb={nsymb}")
        
        sps = fs*tsymb
        output_len = nsymb*sps
        
        if waveform == "PAM":
            data = self.eng.pam_gui(output_len, fs, tsymb, fc, m, var)
        elif waveform == "QAM":
            data = self.eng.mqam_gui(output_len, fs, tsymb, fc, m)

        
        data = np.array(data).flatten()
        
                
        T = len(data)/fs

        t = np.linspace(0,T,len(data))
        
        self.plotting_widget.plot_data(t,data)

        
        
        
        


class SelectionWidget(QWidget):
    def __init__(self):
        super().__init__() 
        
        # Use QGridLayout with 4 columns (label, input, label, input)
        layout = QGridLayout()
        
        # Row 0: Waveform selection (spans all 4 columns)
        waveform_label = QLabel("Waveform:")
        self.waveform_drop_down = QComboBox()
        waveforms = ["PAM", "QAM", "FM"]
        for waveform in waveforms:
            self.waveform_drop_down.addItem(waveform)
        
        layout.addWidget(waveform_label, 0, 0)
        layout.addWidget(self.waveform_drop_down, 0, 1, 1, 3)  # Span 3 columns
        
        # Row 1: fs and Tsymb
        fs_label = QLabel("fs (Hz):")
        self.fs_edit = QLineEdit("48000")
        tsymb_label = QLabel("Tsymb (s):")
        self.tsymb_edit = QLineEdit("0.001")
        
        layout.addWidget(fs_label, 1, 0)
        layout.addWidget(self.fs_edit, 1, 1)
        layout.addWidget(tsymb_label, 1, 2)
        layout.addWidget(self.tsymb_edit, 1, 3)
        
        # Row 2: fc and M
        fc_label = QLabel("fc (Hz):")
        self.fc_edit = QLineEdit("6000")
        m_label = QLabel("M:")
        self.m_edit = QLineEdit("8")
        
        layout.addWidget(fc_label, 2, 0)
        layout.addWidget(self.fc_edit, 2, 1)
        layout.addWidget(m_label, 2, 2)
        layout.addWidget(self.m_edit, 2, 3)
        
        # Row 3: Var and Nsymb
        var_label = QLabel("Var:")
        self.var_edit = QLineEdit("1.0")
        nsymb_label = QLabel("Nsymb:")
        self.nsymb_edit = QLineEdit("2048")
        
        layout.addWidget(var_label, 3, 0)
        layout.addWidget(self.var_edit, 3, 1)
        layout.addWidget(nsymb_label, 3, 2)
        layout.addWidget(self.nsymb_edit, 3, 3)
        
        # Row 4: Run button (span all 4 columns)
        self.button = QPushButton("Run")
        layout.addWidget(self.button, 4, 0, 1, 4)  # row, col, rowspan, colspan
        
        # Set the layout on the widget
        self.setLayout(layout)
    
    
        

class PlottingWidget(QWidget):
    def __init__(self):
        super().__init__()
                
        layout = QVBoxLayout()
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        
        # Add navigation toolbar for interactive controls (zoom, pan, etc.)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Add toolbar and canvas to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Create a button to update/refresh the plot
        self.refresh_button = QPushButton("Refresh Plot")
        self.refresh_button.clicked.connect(self.plot_data)
        layout.addWidget(self.refresh_button)
        
        self.setLayout(layout)
        
        # Initial plot
        self.plot_data()
    
    def plot_data(self, t= None, signal= None):
        """Generate and display a sample plot"""
        # Clear previous plot
        self.figure.clear()
        
        # Create subplot
        ax = self.figure.add_subplot(111)
     
        if (t is not None and signal is not None):
            ax.plot(t, signal, label='Waveform')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Waveform Plot')
            ax.legend()
            ax.grid(True)
        
        # Refresh canvas
        self.canvas.draw()
        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())