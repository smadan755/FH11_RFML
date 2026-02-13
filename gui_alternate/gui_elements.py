# waveform_classes.py
from dataclasses import dataclass
from typing import Optional
import numpy as np
import json
from pathlib import Path
import glob as gb


@dataclass
class WaveformConfig:
    """Configuration for waveform generation with pulse shaping support"""
    modulation: str
    fs: float
    Tsymb: float
    fc: float
    M: int
    Nsymb: int
    var: Optional[float] = None
    freq_sep: Optional[float] = None
    
    # Pulse shaping parameters
    alpha: float = 0.35        # RRC roll-off factor (0 to 1)
    span: int = 8              # Filter span in symbols
    pulse_shape: str = 'rrc'   # 'rrc' or 'rect'
    
    def __post_init__(self):
        """Validate parameters based on MATLAB constraints"""
        # Convert M to int if it's a float like 16.0
        if isinstance(self.M, float) and self.M.is_integer():
            self.M = int(self.M)
        
        # Validate pulse shaping parameters
        if self.alpha < 0 or self.alpha > 1:
            raise ValueError(f"alpha must be between 0 and 1, got {self.alpha}")
        
        if self.pulse_shape not in ['rrc', 'rect']:
            raise ValueError(f"pulse_shape must be 'rrc' or 'rect', got {self.pulse_shape}")
        
        if self.span < 1:
            raise ValueError(f"span must be >= 1, got {self.span}")
        
        self._validate()
    
    def _validate(self):
        """Run validation checks"""
        # Common validations
        sps = self.fs * self.Tsymb
        if abs(sps - round(sps)) > 1e-9:
            raise ValueError(f"fs*Tsymb must be an integer, got {sps}")
        
        if self.fc >= self.fs / 2:
            raise ValueError(f"fc ({self.fc}) must be < fs/2 ({self.fs/2}) to avoid aliasing")
        
        # Note: With pulse shaping, output_len doesn't need to be exactly divisible by sps
        # The MATLAB function handles filter delays internally
        
        # Modulation-specific validations
        if self.modulation == "FSK":
            self._validate_fsk()
        elif self.modulation == "QAM":
            self._validate_qam()
        elif self.modulation == "PAM":
            self._validate_pam()
        elif self.modulation == "PSK":
            self._validate_psk()
        elif self.modulation == "FHSS":
            self._validate_fhss()
        elif self.modulation in ("LFM", "Barker", "FMCW"):
            self._validate_radar()
        elif self.modulation in ("WiFi", "LTE", "5G_NR"):
            self._validate_standard()
        else:
            raise ValueError(f"Unknown modulation type: {self.modulation}")
    
    def _validate_fsk(self):
        """FSK: M must be power of 2"""
        if not self._is_power_of_2(self.M):
            raise ValueError(f"FSK requires M to be a power of 2, got {self.M}")
    
    def _validate_qam(self):
        """QAM: M must be a power of 2 >= 4"""
        if not self._is_power_of_2(self.M):
            raise ValueError(
                f"QAM: M must be a power of 2, got {self.M}. "
                f"Valid values: 4, 16, 32, 64, 128, 256, ..."
            )
        
        if self.M < 4:
            raise ValueError(f"QAM: M must be >= 4, got {self.M}")
    
    def _validate_pam(self):
        """PAM: M must be >= 2"""
        if self.M < 2:
            raise ValueError(f"PAM requires M >= 2, got {self.M}")
        
        # var is optional - MATLAB will handle normalization
    
    def _validate_psk(self):
        """PSK: M must be power of 2"""
        if not self._is_power_of_2(self.M):
            raise ValueError(f"PSK requires M to be a power of 2, got {self.M}")
    
    def _validate_fhss(self):
        """FHSS: M is number of hopping channels, must be >= 2"""
        if self.M < 2:
            raise ValueError(f"FHSS requires M >= 2 hopping channels, got {self.M}")

    def _validate_radar(self):
        """Radar waveforms (LFM, Barker, FMCW): M >= 2"""
        if self.M < 2:
            raise ValueError(f"{self.modulation} requires M >= 2, got {self.M}")

    def _validate_standard(self):
        """Standards-based waveforms (WiFi, LTE, 5G_NR): no strict M requirement"""
        pass  # These use M loosely; MATLAB function handles defaults

    @staticmethod
    def _is_power_of_2(n):
        """Check if n is a power of 2"""
        return n > 0 and (n & (n - 1)) == 0
    
    @property
    def sps(self):
        """Samples per symbol"""
        return int(self.fs * self.Tsymb)
    
    @property
    def output_len(self):
        """Total output length in samples"""
        return self.sps * self.Nsymb
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        config = {
            "modulation": self.modulation,
            "fs": self.fs,
            "Tsymb": self.Tsymb,
            "fc": self.fc,
            "M": self.M,
            "Nsymb": self.Nsymb,
            "sps": self.sps,
            "output_len": self.output_len,
            "alpha": self.alpha,
            "span": self.span,
            "pulse_shape": self.pulse_shape
        }
        
        if self.var is not None:
            config["var"] = self.var
        if self.freq_sep is not None:
            config["freq_sep"] = self.freq_sep
        
        return config
    
    @classmethod
    def from_dict(cls, config_dict):
        """Create config from dictionary"""
        return cls(
            modulation=config_dict['modulation'],
            fs=config_dict['fs'],
            Tsymb=config_dict['Tsymb'],
            fc=config_dict['fc'],
            M=config_dict['M'],
            Nsymb=config_dict['Nsymb'],
            var=config_dict.get('var'),
            freq_sep=config_dict.get('freq_sep'),
            alpha=config_dict.get('alpha', 0.35),
            span=config_dict.get('span', 8),
            pulse_shape=config_dict.get('pulse_shape', 'rrc')
        )


class MATLABGenerator:
    """Handles MATLAB engine calls for waveform generation"""
    
    def __init__(self, matlab_engine):
        if matlab_engine is None:
            raise ValueError("MATLAB engine instance is required")
        self.engine = matlab_engine
    
    def generate(self, config: WaveformConfig):
        """
        Generate waveform using unified MATLAB function
        
        All modulations now use one function!
        """
        # Call unified MATLAB function with name-value pairs
        result = self.engine.waveform_generator(
            float(config.output_len),
            float(config.fs),
            float(config.Tsymb),
            float(config.fc),
            float(config.M),
            config.modulation,
            'alpha', float(config.alpha),
            'span', float(config.span),
            'pulse_shape', config.pulse_shape,
            nargout=1
        )
        
        return np.array(result).flatten()


class Waveform:
    """Main waveform class - maintains backwards compatibility"""
    
    def __init__(self, fs=None, Tsymb=None, Nsymb=None, fc=None, M=None, 
                 modulation=None, var=None, freq_sep=None, eng=None,
                 alpha=0.35, span=8, pulse_shape='rrc'):
        """
        Initialize waveform
        
        Usage:
            # With RRC pulse shaping (default)
            waveform = Waveform(fs=48e3, Tsymb=1e-3, Nsymb=2048, fc=20e3, 
                               M=16, modulation="QAM", eng=eng)
            
            # With rectangular pulses (legacy mode)
            waveform = Waveform(fs=48e3, Tsymb=1e-3, Nsymb=2048, fc=20e3, 
                               M=16, modulation="QAM", eng=eng, 
                               pulse_shape='rect')
        """
        # Create config (this validates parameters)
        self.config = WaveformConfig(
            modulation=modulation,
            fs=fs,
            Tsymb=Tsymb,
            fc=fc,
            M=M,
            Nsymb=Nsymb,
            var=var,
            freq_sep=freq_sep,
            alpha=alpha,
            span=span,
            pulse_shape=pulse_shape
        )
        
        # Store MATLAB generator
        self._generator = MATLABGenerator(eng)
        
        # Data storage
        self._data = None
    
    def generate_data(self):
        """Generate waveform data using MATLAB"""
        self._data = self._generator.generate(self.config)
    
    # Keep your original getter methods for backwards compatibility
    def get_data(self):
        """Get generated data (backwards compatible)"""
        return self._data
    
    def get_fs(self):
        return self.config.fs
    
    def get_fc(self):
        return self.config.fc
    
    def get_M(self):
        return self.config.M
    
    def get_modulation(self):
        return self.config.modulation
    
    def get_Nysmb(self):
        return self.config.Nsymb
    
    def get_Tsymb(self):
        return self.config.Tsymb
    
    def get_var(self):
        return self.config.var
    
    def get_sps(self):
        return self.config.sps
    
    def get_alpha(self):
        return self.config.alpha
    
    def get_span(self):
        return self.config.span
    
    def get_pulse_shape(self):
        return self.config.pulse_shape
    
    # Also add property access (more Pythonic, but optional to use)
    @property
    def data(self):
        """Access data as a property"""
        if self._data is None:
            raise ValueError("Data not generated yet. Call generate_data() first.")
        return self._data
    
    @property
    def fs(self):
        return self.config.fs
    
    @property
    def fc(self):
        return self.config.fc
    
    @property
    def M(self):
        return self.config.M
    
    @property
    def modulation(self):
        return self.config.modulation
    
    @property
    def Nsymb(self):
        return self.config.Nsymb
    
    @property
    def Tsymb(self):
        return self.config.Tsymb
    
    @property
    def var(self):
        return self.config.var
    
    @property
    def sps(self):
        return self.config.sps
    
    @property
    def alpha(self):
        return self.config.alpha
    
    @property
    def span(self):
        return self.config.span
    
    @property
    def pulse_shape(self):
        return self.config.pulse_shape
    
    # File I/O methods
    def to_json(self, rootpath='', datapath='gui/waveform_data'):
        """Save waveform configuration and data to JSON/NPY files"""
        config_name = self._generate_config_name()
        data_folder = Path(rootpath) / datapath / config_name
        data_folder.mkdir(parents=True, exist_ok=True)
        
        # Save config
        config_file = data_folder / "config.json"
        with open(config_file, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=4)
        
        print(f"Config saved to: {config_file}")
        
        # Save data if it exists
        if self._data is None:
            print("No data to save. Call generate_data() first.")
            return self.config.to_dict()
        
        # Find next available data index
        existing_files = list(data_folder.glob("data_*.npy"))
        if existing_files:
            indices = [int(f.stem.split('_')[1]) for f in existing_files]
            next_index = max(indices) + 1
        else:
            next_index = 0
        
        data_file = data_folder / f"data_{next_index}.npy"
        np.save(data_file, self._data)
        print(f"Data saved to: {data_file}")
        
        return self.config.to_dict()
    
    def _generate_config_name(self):
        """Generate a filename-safe config name"""
        config_name = (f"{self.modulation}-M{self.M}-fs{int(self.fs)}-"
                      f"fc{int(self.fc)}-Tsymb{self.Tsymb}-{self.pulse_shape}")
        return config_name.replace('.', '_')
    
    @classmethod
    def from_json(cls, config_name, eng, rootpath='', 
                  datapath='gui/waveform_data', data_index=-1):
        """
        Load waveform from saved configuration
        
        Usage:
            waveform = Waveform.from_json(
                config_name="QAM-M16-fs48000-fc20000-Tsymb0_001-rrc",
                eng=eng,
                rootpath=root,
                data_index=0  # Load first data file
            )
        """
        data_folder = Path(rootpath) / datapath / config_name
        config_file = data_folder / "config.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        # Load config
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        
        config = WaveformConfig.from_dict(config_dict)
        
        # Create waveform instance
        waveform = cls(
            fs=config.fs,
            Tsymb=config.Tsymb,
            Nsymb=config.Nsymb,
            fc=config.fc,
            M=config.M,
            modulation=config.modulation,
            var=config.var,
            freq_sep=config.freq_sep,
            alpha=config.alpha,
            span=config.span,
            pulse_shape=config.pulse_shape,
            eng=eng
        )
        
        # Load data if requested
        if data_index >= 0:
            data_file = data_folder / f"data_{data_index}.npy"
            if data_file.exists():
                waveform._data = np.load(data_file)
                print(f"Loaded data from: {data_file}")
            else:
                print(f"Warning: Data file not found: {data_file}")
        
        print(f"Loaded config from: {config_file}")
        return waveform
    
    # Convenience methods
    def get_time_vector(self):
        """Generate time vector for the waveform"""
        if self._data is None:
            raise ValueError("Data not generated yet. Call generate_data() first.")
        
        T = len(self._data) / self.fs
        return np.linspace(0, T, len(self._data))
    
    def get_duration(self):
        """Get total duration in seconds"""
        if self._data is None:
            raise ValueError("Data not generated yet. Call generate_data() first.")
        return len(self._data) / self.fs