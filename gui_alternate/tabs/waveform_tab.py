from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QSpinBox, QFrame,
                               QSlider, QGridLayout, QTabWidget, QDoubleSpinBox,
                               QLineEdit, QMessageBox, QProgressBar, QScrollArea)
from PySide6.QtCore import Qt

from widgets.waveform_plots import PlottingWidget, FreqDomainPlot, IQDomainPlot, SpectrogramPlot
from gui_elements import Waveform
import numpy as np
import os


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

        # Last generated signal (for Save to Dataset)
        self._last_signal = None
        self._last_modulation = None
        self._gen_thread = None

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
        """Create the RF signal configuration panel (scrollable)"""
        # Inner widget holds all controls
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

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
        layout.addWidget(QLabel("Pulse Shape"))
        self.pulse_shape_combo = QComboBox()
        self.pulse_shape_combo.addItems(["rrc", "rect"])
        self.pulse_shape_combo.setCurrentText("rrc")
        layout.addWidget(self.pulse_shape_combo)

        # --- Action buttons ---
        layout.addSpacing(8)

        generate_btn = QPushButton("▶ Generate Waveform")
        generate_btn.clicked.connect(self.generate_dataset)
        generate_btn.setMinimumHeight(32)
        layout.addWidget(generate_btn)

        # Save / Batch generate
        save_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save to Dataset")
        self.save_btn.setToolTip("Save last generated waveform to waveform_data/<modulation>/")
        self.save_btn.clicked.connect(self.save_to_dataset)
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(32)
        save_layout.addWidget(self.save_btn)

        self.batch_btn = QPushButton("📦 Batch Generate")
        self.batch_btn.setToolTip("Generate N samples per modulation class")
        self.batch_btn.clicked.connect(self.batch_generate)
        self.batch_btn.setMinimumHeight(32)
        save_layout.addWidget(self.batch_btn)
        layout.addLayout(save_layout)

        # Batch generation controls
        batch_ctrl = QHBoxLayout()
        batch_ctrl.addWidget(QLabel("Samples / class:"))
        self.batch_count_spin = QSpinBox()
        self.batch_count_spin.setRange(1, 5000)
        self.batch_count_spin.setValue(50)
        batch_ctrl.addWidget(self.batch_count_spin)
        layout.addLayout(batch_ctrl)

        # Batch progress
        self.batch_progress = QProgressBar()
        self.batch_progress.setTextVisible(True)
        self.batch_progress.setValue(0)
        self.batch_progress.setVisible(False)
        layout.addWidget(self.batch_progress)

        self.batch_status = QLabel("")
        self.batch_status.setProperty("class", "stat-label")
        layout.addWidget(self.batch_status)

        layout.addStretch()

        # Wrap in scroll area
        scroll = QScrollArea()
        scroll.setObjectName("card")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        return scroll
    
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

            # Store for Save to Dataset
            self._last_signal = data
            self._last_modulation = modulation
            self.save_btn.setEnabled(True)

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

    # ------------------------------------------------------------------
    # Dataset saving
    # ------------------------------------------------------------------

    def save_to_dataset(self):
        """Save the last generated waveform to waveform_data/<modulation>/."""
        if self._last_signal is None:
            QMessageBox.information(self, "No Data", "Generate a waveform first.")
            return

        mod = self._last_modulation or "Unknown"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # parent of tabs/
        out_dir = os.path.join(base_dir, 'waveform_data', mod)
        os.makedirs(out_dir, exist_ok=True)

        # Find next index
        existing = [f for f in os.listdir(out_dir) if f.endswith('.npy')]
        idx = len(existing)
        save_path = os.path.join(out_dir, f"data_{idx}.npy")
        np.save(save_path, self._last_signal)
        self.batch_status.setText(f"Saved: {save_path}")

    def batch_generate(self):
        """Launch batch dataset generation across modulation classes."""
        from backend.dataset_generator import DatasetGeneratorThread

        modulations = [self.waveform_combo.itemText(i) for i in range(self.waveform_combo.count())]
        samples = self.batch_count_spin.value()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # parent of tabs/
        out_dir = os.path.join(base_dir, 'waveform_data')

        # Current waveform params as defaults for the generator
        params = {
            'fs': float(self.fs),
            'Tsymb': float(self.Tsymb),
            'Nsymb': int(self.Nsymb),
            'fc': float(self.fc),
            'alpha': float(self.alpha),
            'span': int(self.span),
            'pulse_shape': self.pulse_shape_combo.currentText(),
        }

        self._gen_thread = DatasetGeneratorThread(
            matlab_engine=self.eng,
            modulations=modulations,
            samples_per_class=samples,
            output_dir=out_dir,
            waveform_params=params,
        )
        self._gen_thread.sample_progress.connect(self._on_batch_progress)
        self._gen_thread.generation_finished.connect(self._on_batch_finished)
        self._gen_thread.error_occurred.connect(lambda msg: self.batch_status.setText(msg))

        self.batch_progress.setMaximum(samples * len(modulations))
        self.batch_progress.setValue(0)
        self.batch_progress.setVisible(True)
        self.batch_btn.setEnabled(False)
        self.batch_status.setText("Generating...")
        self._gen_thread.start()

    def _on_batch_progress(self, current, total):
        self.batch_progress.setValue(current)
        self.batch_status.setText(f"Generating: {current}/{total}")

    def _on_batch_finished(self, out_dir):
        self.batch_progress.setVisible(False)
        self.batch_btn.setEnabled(True)
        self.batch_status.setText(f"Done! Dataset saved to {out_dir}")
        if self._gen_thread:
            self._gen_thread.quit()
            self._gen_thread.wait()
            self._gen_thread = None
