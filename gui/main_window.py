from PySide6.QtWidgets import *
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy import signal
import numpy as np
from waveform_functions import *
from gui_elements import *
import matlab.engine
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

load_dotenv()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.eng = matlab.engine.start_matlab()
        
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        waveform_functions_path = os.path.join(current_dir, "waveform_functions")
        
        self.eng.addpath(waveform_functions_path, nargout=0)
        
        # Create central widget with horizontal layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Add SelectionWidget on the left
        self.selection_widget = SelectionWidget()
        main_layout.addWidget(self.selection_widget)
        
        # Add PlottingWidget on the right
        self.plotting_widget = QTabWidget()
        
        self.time_domain_plot = PlottingWidget()
        
        self.freq_domain_plot = FreqDomainPlot()
        self.iq_domain_plot = IQDomainPlot()
        self.spectrogram_plot = SpectrogramPlot() 
        
        self.plotting_widget.addTab(self.time_domain_plot, "Time Domain")
        self.plotting_widget.addTab(self.freq_domain_plot, "Frequency Domain")
        self.plotting_widget.addTab(self.iq_domain_plot, "IQ Plot")
        self.plotting_widget.addTab(self.spectrogram_plot, "Spectrogram")
        
        main_layout.addWidget(self.plotting_widget)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self.setWindowTitle("RFML Waveform Plotter")
        self.resize(1200, 600)
        
        self.selection_widget.button.clicked.connect(self.click_button)
    
    def click_button(self):
        """Handle Run button click - generate and plot waveform"""
        try:
            # Get values from line edits
            modulation = self.selection_widget.waveform_drop_down.currentText()
            fs = float(self.selection_widget.fs_edit.text())
            tsymb = float(self.selection_widget.tsymb_edit.text())
            fc = float(self.selection_widget.fc_edit.text())
            m = float(self.selection_widget.m_edit.text())
            var = float(self.selection_widget.var_edit.text())
            nsymb = int(self.selection_widget.nsymb_edit.text())
            
            # Get pulse shaping parameters
            alpha = float(self.selection_widget.alpha_edit.text())
            span = int(self.selection_widget.span_edit.text())
            pulse_shape = self.selection_widget.pulse_shape_combo.currentText()
            
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
            freqs, ft = self.eng.plotspec_gui(data, 1/fs, nargout=2)
            freqs = np.array(freqs).flatten()
            ft = np.array(ft).flatten()
            
            # Update all plots
            self.time_domain_plot.plot_data(t, data)
            self.freq_domain_plot.plot_data(freqs, np.abs(ft))
            self.spectrogram_plot.plot_data(data, fs, modulation=modulation)
            
            # IQ plot - pass MATLAB engine for matched filter
            self.iq_domain_plot.plot_data(
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
            # Show user-friendly error message for validation errors
            QMessageBox.warning(self, "Invalid Parameters", str(e))
            return
        except Exception as e:
            # Show critical error for unexpected errors
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return


class SelectionWidget(QWidget):
    def __init__(self):
        super().__init__() 
        
        # Use QGridLayout with 4 columns (label, input, label, input)
        layout = QGridLayout()
        
        # Row 0: Waveform selection (spans all 4 columns)
        waveform_label = QLabel("Waveform:")
        self.waveform_drop_down = QComboBox()
        # All supported modulation types from MATLAB waveform_generator
        waveforms = ["PAM", "QAM", "PSK", "FSK", "FHSS"]
        for waveform in waveforms:
            self.waveform_drop_down.addItem(waveform)
        
        layout.addWidget(waveform_label, 0, 0)
        layout.addWidget(self.waveform_drop_down, 0, 1, 1, 3)  # Span 3 columns
        
        self.OFDM_selected = False
        
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
        self.m_edit = QLineEdit("16")
        
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
        
        # Row 4: Pulse shaping parameters
        alpha_label = QLabel("Alpha (RRC):")
        self.alpha_edit = QLineEdit("0.35")
        span_label = QLabel("Span (symbols):")
        self.span_edit = QLineEdit("8")
        
        layout.addWidget(alpha_label, 4, 0)
        layout.addWidget(self.alpha_edit, 4, 1)
        layout.addWidget(span_label, 4, 2)
        layout.addWidget(self.span_edit, 4, 3)
        
        # Row 5: Pulse shape selection
        pulse_shape_label = QLabel("Pulse Shape:")
        self.pulse_shape_combo = QComboBox()
        self.pulse_shape_combo.addItems(["rrc", "rect"])
        
        layout.addWidget(pulse_shape_label, 5, 0)
        layout.addWidget(self.pulse_shape_combo, 5, 1)
        
        # Row 6: Run button (span all 4 columns)
        self.button = QPushButton("Run")
        layout.addWidget(self.button, 6, 0, 1, 4)
        
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
    
    def plot_data(self, t=None, signal=None):
        """Generate and display a sample plot"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
     
        if (t is not None and signal is not None):
            ax.plot(t, signal, label='Waveform')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Waveform Plot')
            ax.legend()
            ax.grid(True)
        
        self.canvas.draw()


class FreqDomainPlot(PlottingWidget):
    def __init__(self):
        super().__init__()
        
    def plot_data(self, freqs=None, fft=None):
        """Generate and display a sample plot"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
     
        if (freqs is not None and fft is not None):
            ax.plot(freqs, fft, label='Waveform')
            ax.set_xlabel('Frequency [Hz]')
            ax.set_ylabel('Magnitude')
            ax.set_title('Frequency Domain')
            ax.legend()
            ax.grid(True)
        
        self.canvas.draw()


class IQDomainPlot(PlottingWidget):
    def __init__(self):
        super().__init__()
        self.refresh_button.hide()
        
    def plot_data(self, data=None, fs=None, fc=None, sps=None, M=None, 
                  modulation=None, alpha=0.35, span=8, pulse_shape='rrc',
                  nsymb=None, eng=None):
        """
        Plot IQ constellation using matched filter approach from MATLAB notebook:
        
        1. Downconvert passband to complex baseband
        2. Apply matched RRC filter: rxFiltered = upfirdn(txWaveform, h, 1)
        3. Account for total delay: span * sps  
        4. Downsample: rxSampled = rxFiltered(totalDelay + 1 : sps : end)
        5. Truncate: rxRecovered = rxSampled(1:numSymbols)
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if data is None or modulation is None:
            ax.text(0.5, 0.5, 'No IQ data to display', 
                   ha='center', va='center', fontsize=14, color='gray')
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            self.canvas.draw()
            return
        
        if modulation == "FSK":
            self._plot_fsk_trajectory(ax, data, fs, fc, sps, M)
        elif modulation == "FHSS":
            self._plot_fhss_trajectory(ax, data, fs, fc, sps, M)
        else:
            self._plot_constellation(ax, data, fs, fc, sps, M, modulation, 
                                     alpha, span, pulse_shape, nsymb, eng)
        
        self.canvas.draw()
    
    def _plot_constellation(self, ax, data, fs, fc, sps, M, modulation,
                            alpha, span, pulse_shape, nsymb, eng):
        """
        Plot constellation using matched filter demodulation.
        Follows exact approach from MATLAB notebook.
        """
        sps = int(sps)
        M = int(M)
        
        # Step 1: Downconvert from passband to complex baseband
        t = np.arange(len(data)) / fs
        complex_baseband = data * np.exp(-1j * 2 * np.pi * fc * t)
        
        # Step 2: Apply matched filter (RRC) which also acts as low-pass
        if pulse_shape == 'rrc' and eng is not None:
            # Use MATLAB to design the same RRC filter
            h = eng.rcosdesign(float(alpha), float(span), float(sps), 'sqrt', nargout=1)
            h = np.array(h).flatten()
            
            # Apply matched filter (this handles both filtering and ISI reduction)
            rxFiltered = np.convolve(complex_baseband, h, mode='full')
            
            # Scale factor of 2 to recover amplitude (from mixing cos²)
            rxFiltered = 2 * rxFiltered
            
            # totalDelay = span * sps (from TX filter + RX matched filter)
            totalDelay = span * sps
            
            # Downsample at optimal sampling instants
            rxSampled = rxFiltered[totalDelay::sps]
            
            # Truncate to number of symbols, excluding edge transients
            if nsymb is not None:
                # Skip first 'span' symbols (TX filter transient) 
                # and last 'span' symbols (RX filter transient)
                skip_symbols = span
                start_idx = skip_symbols
                end_idx = min(nsymb - skip_symbols, len(rxSampled) - skip_symbols)
                
                if end_idx > start_idx:
                    rxRecovered = rxSampled[start_idx:end_idx]
                else:
                    rxRecovered = rxSampled[:nsymb]
            else:
                rxRecovered = rxSampled
            
        else:
            # Rectangular pulse - low-pass filter then downsample
            symbol_rate = fs / sps
            cutoff = symbol_rate / 2 * 0.8  # Tight cutoff for rect
            sos = signal.butter(6, cutoff, 'low', fs=fs, output='sos')
            complex_baseband = 2 * signal.sosfilt(sos, complex_baseband)
            
            offset = sps // 2
            rxRecovered = complex_baseband[offset::sps]
        
        # Normalize to unit average power (matches MATLAB's UnitAveragePower)
        avg_power = np.mean(np.abs(rxRecovered)**2)
        if avg_power > 0:
            rxRecovered = rxRecovered / np.sqrt(avg_power)
        
        I_symbols = np.real(rxRecovered)
        Q_symbols = np.imag(rxRecovered)
        
        # Plot constellation
        ax.scatter(I_symbols, Q_symbols, alpha=0.6, s=20, label='Received Symbols')
        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(f"{M}-{modulation} Constellation Diagram")
        ax.axis('equal')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
        
        # Add ideal constellation points
        if modulation == "QAM":
            self._add_ideal_qam_points(ax, M)
        elif modulation == "PSK":
            self._add_ideal_psk_points(ax, M)
        elif modulation == "PAM":
            self._add_ideal_pam_points(ax, M)
            ax.text(0.98, 0.02, 'PAM: Q ≈ 0 (amplitude modulation only)', 
                   transform=ax.transAxes, fontsize=9, 
                   verticalalignment='bottom', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_fsk_trajectory(self, ax, data, fs, fc, sps, M):
        """Plot FSK frequency trajectory in IQ space"""
        t_demod = np.arange(len(data)) / fs
        
        complex_baseband = data * np.exp(-1j * 2 * np.pi * fc * t_demod)
        
        Tsymb = sps / fs
        freq_sep = 1 / Tsymb
        cutoff = min(M * freq_sep, fc * 0.8, fs / 2 * 0.9)
        sos = signal.butter(4, cutoff, 'low', fs=fs, output='sos')
        complex_baseband = signal.sosfilt(sos, complex_baseband)
        complex_baseband = 2 * complex_baseband
        
        downsample_factor = max(1, int(sps / 10))
        I_viz = np.real(complex_baseband[::downsample_factor])
        Q_viz = np.imag(complex_baseband[::downsample_factor])
        
        time_colors = np.arange(len(I_viz))
        
        scatter = ax.scatter(I_viz, Q_viz, c=time_colors, 
                            cmap='viridis', alpha=0.5, s=10)
        
        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(f"{int(M)}-FSK IQ Trajectory (colored by time)")
        ax.axis('equal')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
        
        self.figure.colorbar(scatter, ax=ax, label='Time')
    
    def _plot_fhss_trajectory(self, ax, data, fs, fc, sps, M):
        """Plot FHSS frequency hopping trajectory in IQ space"""
        t_demod = np.arange(len(data)) / fs
        
        complex_baseband = data * np.exp(-1j * 2 * np.pi * fc * t_demod)
        
        # FHSS has wider bandwidth due to hopping
        channel_spacing = fs / (2 * M)
        hop_bw = channel_spacing * (M - 1)
        cutoff = min(hop_bw * 1.5, fs / 2 * 0.9)
        sos = signal.butter(4, cutoff, 'low', fs=fs, output='sos')
        complex_baseband = signal.sosfilt(sos, complex_baseband)
        complex_baseband = 2 * complex_baseband
        
        # Downsample for visualization
        downsample_factor = max(1, int(sps / 10))
        I_viz = np.real(complex_baseband[::downsample_factor])
        Q_viz = np.imag(complex_baseband[::downsample_factor])
        
        time_colors = np.arange(len(I_viz))
        
        scatter = ax.scatter(I_viz, Q_viz, c=time_colors, 
                            cmap='plasma', alpha=0.5, s=10)
        
        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(f"FHSS IQ Trajectory ({int(M)} channels, colored by time)")
        ax.axis('equal')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
        
        self.figure.colorbar(scatter, ax=ax, label='Time')
    
    def _add_ideal_qam_points(self, ax, M):
        """Add ideal QAM constellation points"""
        M = int(M)
        sqrt_M = int(np.sqrt(M))
        
        if sqrt_M * sqrt_M != M:
            return
        
        levels = np.arange(-(sqrt_M-1), sqrt_M, 2)
        I_ideal, Q_ideal = np.meshgrid(levels, levels)
        I_ideal = I_ideal.flatten()
        Q_ideal = Q_ideal.flatten()
        
        norm_factor = np.sqrt(np.mean(I_ideal**2 + Q_ideal**2))
        I_ideal = I_ideal / norm_factor
        Q_ideal = Q_ideal / norm_factor
        
        ax.scatter(I_ideal, Q_ideal, c='red', marker='x', s=100, 
                  linewidths=2, label='Ideal', zorder=5)
        ax.legend()
    
    def _add_ideal_psk_points(self, ax, M):
        """Add ideal PSK points on unit circle"""
        M = int(M)
        angles = 2 * np.pi * np.arange(M) / M
        I_ideal = np.cos(angles)
        Q_ideal = np.sin(angles)
        
        ax.scatter(I_ideal, Q_ideal, c='red', marker='x', s=100, 
                  linewidths=2, label='Ideal', zorder=5)
        
        theta = np.linspace(0, 2*np.pi, 100)
        ax.plot(np.cos(theta), np.sin(theta), 'g--', alpha=0.3, label='Unit Circle')
        ax.legend()
    
    def _add_ideal_pam_points(self, ax, M):
        """Add ideal PAM levels on I-axis"""
        M = int(M)
        levels = np.arange(-(M-1), M, 2).astype(float)
        
        norm_factor = np.sqrt(np.mean(levels**2))
        if norm_factor > 0:
            levels = levels / norm_factor
        
        ax.scatter(levels, np.zeros_like(levels), c='red', marker='x', 
                  s=100, linewidths=2, label='Ideal PAM Levels', zorder=5)
        
        for level in levels:
            ax.axvline(x=level, color='red', linewidth=0.5, 
                      alpha=0.2, linestyle='--')
        
        ax.legend()


class SpectrogramPlot(PlottingWidget):
    def __init__(self):
        super().__init__()
        
        self.refresh_button.hide()
        self._create_controls()
        
        self.current_x = None
        self.current_fs = None
        self.current_modulation = None
    
    def _create_controls(self):
        """Create minimal control panel"""
        controls_widget = QWidget()
        controls_layout = QHBoxLayout()
        
        cmap_label = QLabel("Color Scheme:")
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(["viridis", "plasma", "inferno", "jet", "hot"])
        
        self.update_button = QPushButton("Refresh")
        self.update_button.clicked.connect(self._update_plot)
        
        controls_layout.addWidget(cmap_label)
        controls_layout.addWidget(self.cmap_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.update_button)
        
        controls_widget.setLayout(controls_layout)
        self.layout().insertWidget(0, controls_widget)
    
    def plot_data(self, x=None, fs=None, modulation=None):
        if x is not None and fs is not None:
            self.current_x = x
            self.current_fs = fs
            self.current_modulation = modulation
            self._update_plot()
    
    def _get_preset(self):
        default = {"nperseg": 1024, "overlap": 0.75, "window": "hann", 
                   "vmin_pct": 5, "vmax_pct": 95}
        
        presets = {
            "PAM": {"nperseg": 512, "overlap": 0.70, "window": "hann", 
                    "vmin_pct": 10, "vmax_pct": 95},
            "QAM": {"nperseg": 1024, "overlap": 0.75, "window": "hann", 
                    "vmin_pct": 5, "vmax_pct": 95},
            "PSK": {"nperseg": 1024, "overlap": 0.75, "window": "hann", 
                    "vmin_pct": 5, "vmax_pct": 95},
            "ASK": {"nperseg": 512, "overlap": 0.70, "window": "hann", 
                    "vmin_pct": 10, "vmax_pct": 95},
            "FSK": {"nperseg": 2048, "overlap": 0.85, "window": "blackman", 
                    "vmin_pct": 3, "vmax_pct": 97},
            "OFDM": {"nperseg": 2048, "overlap": 0.80, "window": "hann", 
                     "vmin_pct": 5, "vmax_pct": 90}
        }
        
        return presets.get(self.current_modulation, default)
    
    def _update_plot(self):
        if self.current_x is None or self.current_fs is None:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        x = self.current_x
        fs = self.current_fs
        
        if np.iscomplexobj(x):
            x = np.real(x)
        
        preset = self._get_preset()
        
        nperseg = preset["nperseg"]
        noverlap = int(nperseg * preset["overlap"])
        
        f, t, Sxx = signal.spectrogram(
            x, fs=fs, window=preset["window"],
            nperseg=nperseg, noverlap=noverlap,
            scaling='density', mode='psd'
        )
        
        Sxx_dB = 10 * np.log10(Sxx + 1e-10)
        
        vmin = np.percentile(Sxx_dB, preset["vmin_pct"])
        vmax = np.percentile(Sxx_dB, preset["vmax_pct"])
        
        im = ax.pcolormesh(t, f, Sxx_dB, shading='gouraud',
                          cmap=self.cmap_combo.currentText(),
                          vmin=vmin, vmax=vmax)
        
        self.figure.colorbar(im, ax=ax, label='Power/Frequency (dB/Hz)')
        
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Frequency [Hz]")
        
        if self.current_modulation:
            ax.set_title(f"{self.current_modulation} Spectrogram")
        else:
            ax.set_title("Spectrogram")
        
        ax.set_ylim(0, fs/2)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())