from PySide6.QtCore import QThread, Signal
import numpy as np
import os


class DatasetGeneratorThread(QThread):
    """Generate N waveform samples per modulation class using the MATLAB engine.

    Saves each sample to: <output_dir>/<ModulationType>/data_<index>.npy
    Emits `sample_progress` after each sample and `generation_finished` when done.
    """
    sample_progress = Signal(int, int)      # (current_count, total_count)
    generation_finished = Signal(str)       # output directory path
    error_occurred = Signal(str)            # error message

    def __init__(self, matlab_engine, modulations, samples_per_class, output_dir, waveform_params=None):
        """
        Args:
            matlab_engine: Shared MATLAB engine wrapper (backend.matlab_engine.MatlabEngine)
            modulations: list of modulation type strings, e.g. ['PAM', 'QAM', 'PSK']
            samples_per_class: int — number of samples to generate for each modulation
            output_dir: base directory to write class folders into
            waveform_params: dict of default waveform parameters; individual fields may be
                             randomized per sample inside `_randomize_params`.
        """
        super().__init__()
        self.matlab_engine = matlab_engine
        self.modulations = list(modulations)
        self.samples_per_class = int(samples_per_class)
        self.output_dir = output_dir
        self.waveform_params = waveform_params or {}
        self._stop = False

    def stop(self):
        self._stop = True

    # Default parameter ranges used when the user does not specify overrides
    _DEFAULTS = {
        'fs':          100e3,
        'Tsymb':       1e-3,
        'Nsymb':       128,
        'fc':          10e3,
        'alpha':       0.35,
        'span':        8,
        'pulse_shape': 'rrc',
    }

    # How M maps to each modulation
    _M_MAP = {
        'PAM':  [2, 4, 8],
        'QAM':  [4, 16, 64],
        'PSK':  [2, 4, 8],
        'FSK':  [2, 4, 8],
        'OFDM': [4, 16, 64],
    }

    # Variance range for additive noise
    _VAR_RANGE = (0.001, 0.05)

    def _randomize_params(self, modulation):
        """Return a dict of waveform parameters with light randomization."""
        rng = np.random.default_rng()

        params = dict(self._DEFAULTS)
        params.update(self.waveform_params)  # user overrides

        # Pick a random M for the modulation type
        m_choices = self._M_MAP.get(modulation, [4])
        params['M'] = int(rng.choice(m_choices))

        # Randomize noise variance
        params['var'] = float(rng.uniform(*self._VAR_RANGE))

        # Small jitter on carrier frequency (±10 %)
        base_fc = params.get('fc', 10e3)
        params['fc'] = float(base_fc * rng.uniform(0.9, 1.1))

        params['modulation'] = modulation

        # FSK specific
        if modulation == 'FSK':
            params['freq_sep'] = float(params.get('freq_sep', 1000))

        return params

    def run(self):
        from gui_elements import Waveform  # same class used by the Waveform tab

        total = self.samples_per_class * len(self.modulations)
        count = 0

        for mod in self.modulations:
            class_dir = os.path.join(self.output_dir, mod)
            os.makedirs(class_dir, exist_ok=True)

            for i in range(self.samples_per_class):
                if self._stop:
                    self.generation_finished.emit(self.output_dir)
                    return

                try:
                    params = self._randomize_params(mod)
                    waveform = Waveform(
                        fs=params['fs'],
                        Tsymb=params['Tsymb'],
                        Nsymb=params['Nsymb'],
                        fc=params['fc'],
                        M=params['M'],
                        modulation=params['modulation'],
                        var=params.get('var'),
                        eng=self.matlab_engine,
                        alpha=params.get('alpha', 0.35),
                        span=params.get('span', 8),
                        pulse_shape=params.get('pulse_shape', 'rrc'),
                    )
                    waveform.generate_data()
                    data = waveform.get_data()

                    save_path = os.path.join(class_dir, f"data_{i}.npy")
                    np.save(save_path, data)

                except Exception as e:
                    print(f"Error generating {mod} sample {i}: {e}")
                    self.error_occurred.emit(f"Error generating {mod} sample {i}: {e}")

                count += 1
                self.sample_progress.emit(count, total)

        self.generation_finished.emit(self.output_dir)
