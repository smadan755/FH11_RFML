from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QSpinBox, QFrame,
                               QSlider, QGridLayout, QTabWidget, QDoubleSpinBox,
                               QLineEdit, QMessageBox)
from PySide6.QtCore import Qt

from widgets.waveform_plots import PlottingWidget, FreqDomainPlot, IQDomainPlot, SpectrogramPlot
from gui_elements import Waveform
import numpy as np


class WaveformSelectionTab(QWidget):
    """Waveform configuration and visualization tab"""
    def __init__(self, eng, parent=None):
        super().__init__(parent)
        self.eng = eng  # Raw MATLAB engine (matlab.engine)
        
        # Core parameters — match original GUI defaults
        self.fs = 48000       # Hz
        self.Tsymb = 0.001    # seconds
        self.fc = 6000        # Hz
        self.M = 16
        self.var = 1.0
        self.Nsymb = 2048
        self.alpha = 0.35
        self.span = 8         # symbols
        self.modulation = "PAM"

        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QHBoxLayout(self)
        #layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel - RF Signal Configuration
        left_panel = self.create_configuration_panel()
        layout.addWidget(left_panel, 1)
        
        right_panel = self.create_visualizations_panel()
        layout.addWidget(right_panel, 2)
    
    def create_configuration_panel(self):
        """Create the RF signal configuration panel"""
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        
        # Title
        #title_layout = QVBoxLayout()
        #title = QLabel("📡 RF Signal Configuration")
        #title.setProperty("class", "section-title")
        #subtitle = QLabel("Configure signal generation parameters")
        #subtitle.setProperty("class", "section-subtitle")
        #title_layout.addWidget(title)
        #title_layout.addWidget(subtitle)
        #title_layout.setSpacing(4)
        #layout.addLayout(title_layout)

        # Waveform (Modulation Type)
        layout.addWidget(QLabel("Waveform"))
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(["PAM", "QAM", "PSK", "FSK", "FHSS"])
        layout.addWidget(self.waveform_combo)

        # fs
        layout.addWidget(QLabel("Sampling Frequency fs (Hz)"))
        self.fs_spin = QDoubleSpinBox()
        self.fs_spin.setRange(1, 1e9)
        self.fs_spin.setDecimals(0)
        self.fs_spin.setSingleStep(1000)
        self.fs_spin.setValue(self.fs)
        self.fs_spin.valueChanged.connect(lambda v: setattr(self, "fs", v))
        layout.addWidget(self.fs_spin)

        # fc
        layout.addWidget(QLabel("Carrier Frequency fc (Hz)"))
        self.fc_spin = QDoubleSpinBox()
        self.fc_spin.setRange(0, 1e9)
        self.fc_spin.setDecimals(0)
        self.fc_spin.setSingleStep(1000)
        self.fc_spin.setValue(self.fc)
        self.fc_spin.valueChanged.connect(lambda v: setattr(self, "fc", v))
        layout.addWidget(self.fc_spin)

        # var
        layout.addWidget(QLabel("Noise Variance"))
        self.var_spin = QDoubleSpinBox()
        self.var_spin.setRange(0.0, 10.0)
        self.var_spin.setSingleStep(0.1)
        self.var_spin.setValue(self.var)
        self.var_spin.valueChanged.connect(lambda v: setattr(self, "var", v))
        layout.addWidget(self.var_spin)

        # alpha
        layout.addWidget(QLabel("RRC Roll-off α"))
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setValue(self.alpha)
        self.alpha_spin.valueChanged.connect(lambda v: setattr(self, "alpha", v))
        layout.addWidget(self.alpha_spin)


        # Tsymb
        layout.addWidget(QLabel("Symbol Period Tsymb (s)"))
        self.tsymb_spin = QDoubleSpinBox()
        self.tsymb_spin.setRange(1e-7, 1.0)
        self.tsymb_spin.setDecimals(6)
        self.tsymb_spin.setSingleStep(0.0001)
        self.tsymb_spin.setValue(self.Tsymb)
        self.tsymb_spin.valueChanged.connect(lambda v: setattr(self, "Tsymb", v))
        layout.addWidget(self.tsymb_spin)


        # M
        layout.addWidget(QLabel("Modulation Order M"))
        self.M_spin = QDoubleSpinBox()
        self.M_spin.setRange(2, 256)
        self.M_spin.setDecimals(0)
        self.M_spin.setSingleStep(1)
        self.M_spin.setValue(self.M)
        self.M_spin.valueChanged.connect(lambda v: setattr(self, "M", v))
        layout.addWidget(self.M_spin)

        # Nsymb
        layout.addWidget(QLabel("Number of Symbols"))
        self.nsymb_spin = QDoubleSpinBox()
        self.nsymb_spin.setRange(16, 10000)
        self.nsymb_spin.setDecimals(0)
        self.nsymb_spin.setSingleStep(1)
        self.nsymb_spin.setValue(self.Nsymb)
        self.nsymb_spin.valueChanged.connect(lambda v: setattr(self, "Nsymb", v))
        layout.addWidget(self.nsymb_spin)

        # span
        layout.addWidget(QLabel("Pulse Span (symbols)"))
        self.span_spin = QDoubleSpinBox()
        self.span_spin.setRange(2, 50)
        self.span_spin.setDecimals(0)
        self.span_spin.setSingleStep(1)
        self.span_spin.setValue(self.span)
        self.span_spin.valueChanged.connect(lambda v: setattr(self, "span", v))
        layout.addWidget(self.span_spin)

        # Pulse Shape
        pulse_label = QLabel("Pulse Shape")
        layout.addWidget(pulse_label)

        self.pulse_shape_combo = QComboBox()
        self.pulse_shape_combo.addItems(["rrc", "rect"])
        self.pulse_shape_combo.setCurrentText("rrc")
        layout.addWidget(self.pulse_shape_combo)

        #layout.addStretch()


        generate_btn = QPushButton("▶ Generate Dataset")
        generate_btn.clicked.connect(self.generate_dataset)
        layout.addWidget(generate_btn)
        
        return panel
    
    def create_slider_control(self, label, value, unit, min_val, max_val, attr_name):
        """Create a slider control with label and value display"""
        container = QVBoxLayout()
        container.setSpacing(8)
        
        # Label and value
        header = QHBoxLayout()
        label_widget = QLabel(label)
        value_label = QLabel(f"{value} {unit}")
        value_label.setProperty("class", "stat-value")
        value_label.setMinimumHeight(24)
        header.addWidget(label_widget)
        header.addStretch()
        header.addWidget(value_label)
        container.addLayout(header)
        
        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(value)
        
        def update_value(v):
            value_label.setText(f"{v} {unit}")
            setattr(self, attr_name, v)
            self.update_waveform_plots()
        
        slider.valueChanged.connect(update_value)
        container.addWidget(slider)
        
        return container
    
    def create_visualizations_panel(self):
        """Create the visualizations panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        
        self.plot_tabs = QTabWidget()
        self.waveform_plot = PlottingWidget()
        self.freq_plot = FreqDomainPlot()
        self.constellation_plot = IQDomainPlot()
        self.spectrogram_plot = SpectrogramPlot()

        self.plot_tabs.addTab(self.waveform_plot, "Waveform")
        self.plot_tabs.addTab(self.freq_plot, "Frequency")
        self.plot_tabs.addTab(self.constellation_plot, "Constellation")
        self.plot_tabs.addTab(self.spectrogram_plot, "Spectrogram")

        layout.addWidget(self.plot_tabs)
        
        return panel

    def generate_dataset(self):
        """Generate and plot waveform — mirrors original GUI's click_button()"""
        try:
            modulation = self.waveform_combo.currentText()
            fs = float(self.fs)
            tsymb = float(self.Tsymb)
            fc = float(self.fc)
            m = float(self.M)
            var = float(self.var)
            nsymb = int(self.Nsymb)
            alpha = float(self.alpha)
            span = int(self.span)
            pulse_shape = self.pulse_shape_combo.currentText()

            print(f"Running: {modulation}")
            print(f"Parameters: fs={fs}, Tsymb={tsymb}, fc={fc}, M={m}, Var={var}, Nsymb={nsymb}")
            print(f"Pulse Shaping: alpha={alpha}, span={span}, pulse_shape={pulse_shape}")

            # Create waveform (validation happens here)
            waveform = Waveform(
                fs=fs,
                Tsymb=tsymb,
                Nsymb=nsymb,
                fc=fc,
                M=m,
                modulation=modulation,
                var=var,
                eng=self.eng,
                alpha=alpha,
                span=span,
                pulse_shape=pulse_shape
            )

            # Generate the waveform data
            waveform.generate_data()
            data = waveform.get_data()

            # Get waveform parameters
            sps = waveform.get_sps()
            T = len(data) / fs
            t = np.linspace(0, T, len(data))

            # Compute frequency spectrum using MATLAB
            freqs, ft = self.eng.plotspec_gui(data, 1 / fs, nargout=2)
            freqs = np.array(freqs).flatten()
            ft = np.array(ft).flatten()

            # Update all plots
            self.waveform_plot.plot_data(t, data)
            self.freq_plot.plot_data(freqs, np.abs(ft))
            self.spectrogram_plot.plot_data(data, fs, modulation=modulation)

            # IQ plot — pass MATLAB engine for matched filter
            self.constellation_plot.plot_data(
                data=data,
                fs=fs,
                fc=fc,
                sps=sps,
                M=m,
                modulation=modulation,
                alpha=alpha,
                span=span,
                pulse_shape=pulse_shape,
                nsymb=nsymb,
                eng=self.eng
            )

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Parameters", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


