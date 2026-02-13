from PySide6.QtWidgets import QGridLayout, QWidget, QLabel, QComboBox, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy import signal

_DARK_BG = '#1e1e32'
_DARK_AXES = '#2d2d44'
_DARK_TEXT = '#e0e0e0'
_DARK_GRID = '#404060'


def _apply_dark_style(fig):
    """Apply dark theme colors to a matplotlib figure."""
    fig.patch.set_facecolor(_DARK_BG)
    for ax in fig.axes:
        ax.set_facecolor(_DARK_AXES)
        ax.tick_params(colors=_DARK_TEXT)
        ax.xaxis.label.set_color(_DARK_TEXT)
        ax.yaxis.label.set_color(_DARK_TEXT)
        ax.title.set_color(_DARK_TEXT)
        for spine in ax.spines.values():
            spine.set_color(_DARK_GRID)
        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(_DARK_AXES)
            legend.get_frame().set_edgecolor(_DARK_GRID)
            for text in legend.get_texts():
                text.set_color(_DARK_TEXT)


class PlottingWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), facecolor=_DARK_BG)
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
    
    def plot_data(self, t=None, signal=None, modulation=None):
        """Generate and display a sample plot"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
     
        if (t is not None and signal is not None):
            ax.plot(t, signal, color='#818cf8', label=f'Waveform: {modulation}')
            ax.set_xlabel('Time (μs)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Waveform Plot')
            ax.legend(facecolor=_DARK_AXES, edgecolor=_DARK_GRID, labelcolor=_DARK_TEXT)
            ax.grid(True, color=_DARK_GRID, alpha=0.3)

        _apply_dark_style(self.figure)
        self.canvas.draw()


class FreqDomainPlot(PlottingWidget):
    def __init__(self):
        super().__init__()

    def plot_data(self, freqs=None, fft=None, modulation = None):
        """Generate and display a sample plot"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if (freqs is not None and fft is not None):
            ax.plot(freqs, fft, color='#818cf8', label=f'Waveform: {modulation}')
            ax.set_xlabel('Frequency [MHz]')
            ax.set_ylabel('Magnitude')
            ax.set_title('Frequency Domain')
            ax.legend(facecolor=_DARK_AXES, edgecolor=_DARK_GRID, labelcolor=_DARK_TEXT)
            ax.grid(True, color=_DARK_GRID, alpha=0.3)

        _apply_dark_style(self.figure)
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
                   ha='center', va='center', fontsize=14, color='#9ca3af')
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            _apply_dark_style(self.figure)
            self.canvas.draw()
            return
        
        if modulation == "FSK":
            self._plot_fsk_trajectory(ax, data, fs, fc, sps, M)
        elif modulation == "FHSS":
            self._plot_fhss_trajectory(ax, data, fs, fc, sps, M)
        elif modulation in ("LFM", "FMCW"):
            self._plot_chirp_iq(ax, data, fs, fc, modulation, M)
        elif modulation == "Barker":
            self._plot_phase_coded_iq(ax, data, fs, fc, modulation, M)
        elif modulation in ("WiFi", "LTE", "5G_NR"):
            self._plot_ofdm_constellation(ax, data, fs, fc, modulation)
        else:
            self._plot_constellation(ax, data, fs, fc, sps, M, modulation,
                                     alpha, span, pulse_shape, nsymb, eng)

        _apply_dark_style(self.figure)
        # Style colorbar text if present
        for cbar_ax in self.figure.axes[1:]:
            cbar_ax.tick_params(colors=_DARK_TEXT)
            cbar_ax.yaxis.label.set_color(_DARK_TEXT)
        self.figure.tight_layout()
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
                skip_symbols = int(span)
                start_idx = int(skip_symbols)
                end_idx = int(min(nsymb - skip_symbols, len(rxSampled) - skip_symbols))
                
                if end_idx > start_idx:
                    rxRecovered = rxSampled[start_idx:end_idx]
                else:
                    rxRecovered = rxSampled[:int(nsymb)]
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
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        
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
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        
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
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        
        self.figure.colorbar(scatter, ax=ax, label='Time')
    
    # ------------------------------------------------------------------
    # Radar waveforms: chirp IQ trajectory
    # ------------------------------------------------------------------

    def _plot_chirp_iq(self, ax, data, fs, fc, modulation, M):
        """
        Plot IQ trajectory for chirp-type radar waveforms (LFM, FMCW).

        These signals sweep in frequency, so the IQ trajectory traces out
        a spiral pattern. We downconvert to baseband, low-pass filter,
        then plot I vs Q colored by time to show the frequency sweep.
        """
        t_demod = np.arange(len(data)) / fs

        # Downconvert to complex baseband
        complex_baseband = data * np.exp(-1j * 2 * np.pi * fc * t_demod)

        # Low-pass filter — chirp bandwidth is roughly M * 100 kHz
        bw_est = max(M * 1e5, fs * 0.1)  # At least 10% of fs
        cutoff = min(bw_est * 0.6, fs / 2 * 0.9)
        sos = signal.butter(4, cutoff, 'low', fs=fs, output='sos')
        complex_baseband = 2 * signal.sosfilt(sos, complex_baseband)

        # Downsample for cleaner visualization
        downsample_factor = max(1, len(complex_baseband) // 5000)
        I_viz = np.real(complex_baseband[::downsample_factor])
        Q_viz = np.imag(complex_baseband[::downsample_factor])

        # Normalize
        max_amp = max(np.max(np.abs(I_viz)), np.max(np.abs(Q_viz)), 1e-10)
        I_viz /= max_amp
        Q_viz /= max_amp

        time_colors = np.arange(len(I_viz))

        scatter = ax.scatter(I_viz, Q_viz, c=time_colors,
                            cmap='coolwarm', alpha=0.6, s=8)

        # Also plot the trajectory as a thin line to show the spiral
        ax.plot(I_viz, Q_viz, color='#818cf8', alpha=0.15, linewidth=0.5)

        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(f"{modulation} IQ Trajectory (chirp sweep, M={int(M)})")
        ax.axis('equal')
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)

        self.figure.colorbar(scatter, ax=ax, label='Time →')

        # Add annotation about what the plot shows
        ax.text(0.02, 0.98, 'Frequency sweep → spiral trajectory',
               transform=ax.transAxes, fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def _plot_phase_coded_iq(self, ax, data, fs, fc, modulation, M):
        """
        Plot IQ for phase-coded radar waveforms (Barker codes).

        Barker codes use discrete phase shifts (0° / 180° for binary codes).
        We downconvert and show symbol-rate samples to reveal the phase states.
        """
        t_demod = np.arange(len(data)) / fs

        # Downconvert to complex baseband
        complex_baseband = data * np.exp(-1j * 2 * np.pi * fc * t_demod)

        # Low-pass filter — bandwidth ~ 2 * chip_rate
        # Barker chip rate is roughly fs / (output_len / M)
        cutoff = min(fs * 0.15, fs / 2 * 0.9)
        sos = signal.butter(4, cutoff, 'low', fs=fs, output='sos')
        complex_baseband = 2 * signal.sosfilt(sos, complex_baseband)

        # Downsample for visualization
        downsample_factor = max(1, len(complex_baseband) // 3000)
        I_viz = np.real(complex_baseband[::downsample_factor])
        Q_viz = np.imag(complex_baseband[::downsample_factor])

        # Normalize
        max_amp = max(np.max(np.abs(I_viz)), np.max(np.abs(Q_viz)), 1e-10)
        I_viz /= max_amp
        Q_viz /= max_amp

        time_colors = np.arange(len(I_viz))

        scatter = ax.scatter(I_viz, Q_viz, c=time_colors,
                            cmap='viridis', alpha=0.6, s=12)

        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(f"Barker-{int(M)} IQ Diagram (phase-coded)")
        ax.axis('equal')
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)

        # Add ideal BPSK-like constellation points for reference
        ax.scatter([1, -1], [0, 0], c='red', marker='x', s=100,
                  linewidths=2, label='Ideal phases (0°, 180°)', zorder=5)
        ax.legend(fontsize=8)

        self.figure.colorbar(scatter, ax=ax, label='Time →')

        ax.text(0.02, 0.98, f'Barker code: {int(M)} chips (binary phase)',
               transform=ax.transAxes, fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # ------------------------------------------------------------------
    # OFDM-based waveforms: WiFi, LTE, 5G NR constellation
    # ------------------------------------------------------------------

    def _plot_ofdm_constellation(self, ax, data, fs, fc, modulation):
        """
        Plot OFDM subcarrier constellation for WiFi, LTE, 5G NR.

        These waveforms use OFDM with QAM modulation on each subcarrier.
        We downconvert to baseband, then perform FFT per OFDM symbol to
        recover the per-subcarrier constellation points.
        """
        t_demod = np.arange(len(data)) / fs

        # Downconvert to complex baseband
        complex_baseband = data * np.exp(-1j * 2 * np.pi * fc * t_demod)

        # Low-pass filter — use wider bandwidth for OFDM signals
        cutoff = min(fs * 0.4, fs / 2 * 0.95)
        sos = signal.butter(6, cutoff, 'low', fs=fs, output='sos')
        complex_baseband = 2 * signal.sosfilt(sos, complex_baseband)

        # Estimate OFDM symbol length based on modulation type
        # Standard OFDM FFT sizes
        ofdm_params = {
            'WiFi':  {'nfft': 64,   'cp_len': 16},   # 802.11a/n/ac/ax
            'LTE':   {'nfft': 128,  'cp_len': 9},     # LTE 1.4 MHz (128 subcarriers)
            '5G_NR': {'nfft': 256,  'cp_len': 18},    # 5G NR with 256 subcarriers
        }

        params = ofdm_params.get(modulation, {'nfft': 64, 'cp_len': 16})
        nfft = params['nfft']
        cp_len = params['cp_len']
        sym_len = nfft + cp_len  # Total OFDM symbol length including CP

        # Try to extract OFDM symbols via FFT
        # The signal may have been resampled, so scale the FFT size
        # to match the actual sample rate
        n_symbols = len(complex_baseband) // sym_len

        if n_symbols < 1:
            # Signal is too short for OFDM demod; fall back to raw IQ scatter
            self._plot_raw_iq_scatter(ax, complex_baseband, modulation)
            return

        # Extract constellation points from each OFDM symbol
        all_points = []
        for i in range(min(n_symbols, 50)):  # Cap at 50 symbols for performance
            start = i * sym_len + cp_len  # Skip cyclic prefix
            end = start + nfft
            if end > len(complex_baseband):
                break

            # FFT to get subcarrier values
            symbol_freq = np.fft.fft(complex_baseband[start:end]) / np.sqrt(nfft)

            # Keep only the active subcarriers (center ~75%)
            n_active = int(nfft * 0.75)
            half = n_active // 2
            # Positive subcarriers + negative subcarriers (skip DC)
            active = np.concatenate([
                symbol_freq[1:half+1],
                symbol_freq[-half:]
            ])
            all_points.extend(active)

        if len(all_points) == 0:
            self._plot_raw_iq_scatter(ax, complex_baseband, modulation)
            return

        constellation = np.array(all_points)

        # Normalize to unit average power
        avg_power = np.mean(np.abs(constellation)**2)
        if avg_power > 0:
            constellation = constellation / np.sqrt(avg_power)

        I_pts = np.real(constellation)
        Q_pts = np.imag(constellation)

        # Color by symbol index for visual richness
        n_per_sym = len(all_points) // max(n_symbols, 1)
        if n_per_sym > 0:
            sym_colors = np.repeat(np.arange(len(all_points) // n_per_sym + 1), n_per_sym)[:len(all_points)]
        else:
            sym_colors = np.arange(len(all_points))

        scatter = ax.scatter(I_pts, Q_pts, c=sym_colors, cmap='viridis',
                            alpha=0.4, s=8, edgecolors='none')

        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')

        display_names = {
            'WiFi': 'WiFi 802.11ax',
            'LTE': 'LTE Downlink',
            '5G_NR': '5G NR Downlink'
        }
        ax.set_title(f"{display_names.get(modulation, modulation)} OFDM Constellation")
        ax.axis('equal')
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)

        self.figure.colorbar(scatter, ax=ax, label='OFDM Symbol #')

        ax.text(0.02, 0.98, f'FFT size: {nfft}, CP: {cp_len} samples',
               transform=ax.transAxes, fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def _plot_raw_iq_scatter(self, ax, complex_baseband, modulation):
        """Fallback: raw IQ scatter when OFDM demod fails."""
        # Downsample for visualization
        downsample_factor = max(1, len(complex_baseband) // 5000)
        I_viz = np.real(complex_baseband[::downsample_factor])
        Q_viz = np.imag(complex_baseband[::downsample_factor])

        # Normalize
        avg_power = np.mean(I_viz**2 + Q_viz**2)
        if avg_power > 0:
            scale = np.sqrt(avg_power)
            I_viz /= scale
            Q_viz /= scale

        time_colors = np.arange(len(I_viz))
        scatter = ax.scatter(I_viz, Q_viz, c=time_colors, cmap='viridis',
                            alpha=0.4, s=8, edgecolors='none')

        ax.set_xlabel('In-phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(f"{modulation} Raw IQ Scatter")
        ax.axis('equal')
        ax.grid(True, color=_DARK_GRID, alpha=0.3)
        ax.axhline(y=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color=_DARK_GRID, linewidth=0.5, alpha=0.5)

        self.figure.colorbar(scatter, ax=ax, label='Time →')

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
                     "vmin_pct": 5, "vmax_pct": 90},
            # Radar waveforms
            "LFM":    {"nperseg": 512,  "overlap": 0.90, "window": "hann",
                       "vmin_pct": 3, "vmax_pct": 97},
            "Barker": {"nperseg": 256,  "overlap": 0.85, "window": "hann",
                       "vmin_pct": 5, "vmax_pct": 95},
            "FMCW":   {"nperseg": 512,  "overlap": 0.90, "window": "hann",
                       "vmin_pct": 3, "vmax_pct": 97},
            # Standards-based
            "WiFi":   {"nperseg": 2048, "overlap": 0.80, "window": "hann",
                       "vmin_pct": 5, "vmax_pct": 92},
            "LTE":    {"nperseg": 2048, "overlap": 0.80, "window": "hann",
                       "vmin_pct": 5, "vmax_pct": 92},
            "5G_NR":  {"nperseg": 2048, "overlap": 0.80, "window": "hann",
                       "vmin_pct": 5, "vmax_pct": 92},
            "FHSS":   {"nperseg": 2048, "overlap": 0.85, "window": "blackman",
                       "vmin_pct": 3, "vmax_pct": 97}
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

        if len(x) < nperseg:
            nperseg = len(x)
    
        noverlap = int(nperseg * preset["overlap"])

        if noverlap >= nperseg:
            noverlap = nperseg - 1
        
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
        ax.grid(True, color=_DARK_GRID, alpha=0.3, linestyle='--')

        _apply_dark_style(self.figure)
        # Also style the colorbar text
        for cbar_ax in self.figure.axes[1:]:
            cbar_ax.tick_params(colors=_DARK_TEXT)
            cbar_ax.yaxis.label.set_color(_DARK_TEXT)

        self.figure.tight_layout()
        self.canvas.draw()
