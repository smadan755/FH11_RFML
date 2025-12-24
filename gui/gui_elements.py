# waveform_classes.py
from dataclasses import dataclass
from typing import Optional
import numpy as np
import json
from pathlib import Path
import glob as gb


@dataclass
class WaveformConfig:
    """Configuration for waveform generation with built-in validation"""
    modulation: str
    fs: float
    Tsymb: float
    fc: float
    M: int
    Nsymb: int
    var: Optional[float] = None
    freq_sep: Optional[float] = None
    
    def __post_init__(self):
        """Validate parameters based on MATLAB constraints"""
        # Convert M to int if it's a float like 16.0
        if isinstance(self.M, float) and self.M.is_integer():
            self.M = int(self.M)
        
        self._validate()
    
    def _validate(self):
        """Run validation checks"""
        # Common validations
        sps = self.fs * self.Tsymb
        if abs(sps - round(sps)) > 1e-9:
            raise ValueError(f"fs*Tsymb must be an integer, got {sps}")
        
        if self.fc >= self.fs / 2:
            raise ValueError(f"fc ({self.fc}) must be < fs/2 ({self.fs/2}) to avoid aliasing")
        
        output_len = self.output_len
        if output_len % self.sps != 0:
            raise ValueError(f"output_len must be divisible by sps")
        
        # Modulation-specific validations
        if self.modulation == "FSK":
            self._validate_fsk()
        elif self.modulation == "QAM":
            self._validate_qam()
        elif self.modulation == "PAM":
            self._validate_pam()
        else:
            raise ValueError(f"Unknown modulation type: {self.modulation}")
    
    def _validate_fsk(self):
        """FSK: M must be power of 2, fs*Tsymb/log2(M) must be integer"""
        if not self._is_power_of_2(self.M):
            raise ValueError(f"FSK requires M to be a power of 2, got {self.M}")
        
        bits_per_symbol = int(np.log2(self.M))
        if self.sps % bits_per_symbol != 0:
            raise ValueError(
                f"FSK requires fs*Tsymb/log2(M) to be integer: "
                f"{self.sps}/{bits_per_symbol} = {self.sps/bits_per_symbol}"
            )
    
    def _validate_qam(self):
        """
        QAM: M must be a power of 2 (for bit mapping)
        Square QAM: M = 4, 16, 64, 256, ... (sqrt(M) integer)
        Cross QAM: M = 32, 128, 512, ... (sqrt(M) not integer)
        """
        # Must be power of 2
        if not self._is_power_of_2(self.M):
            raise ValueError(
                f"QAM: M must be a power of 2, got {self.M}. "
                f"Valid values: 4, 16, 32, 64, 128, 256, ..."
            )
        
        # Must be at least 4
        if self.M < 4:
            raise ValueError(f"QAM: M must be >= 4, got {self.M}")
        
        # Check samples per symbol divisibility
        sps = int(self.fs * self.Tsymb)
        bits_per_symbol = int(np.log2(self.M))
        
        if sps % bits_per_symbol != 0:
            raise ValueError(
                f"QAM requires fs*Tsymb/log2(M) to be integer: "
                f"{sps}/{bits_per_symbol} = {sps/bits_per_symbol}"
            )
        
    def _validate_pam(self):
        """PAM: M must be even integer >= 2, var must be specified"""
        if self.M < 2 or self.M % 2 != 0:
            raise ValueError(f"PAM requires M to be even integer >= 2, got {self.M}")
        
        if self.var is None:
            raise ValueError("PAM requires 'var' parameter to be specified")
    
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
            "output_len": self.output_len
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
            freq_sep=config_dict.get('freq_sep')
        )


class MATLABGenerator:
    """Handles MATLAB engine calls for waveform generation"""
    
    def __init__(self, matlab_engine):
        if matlab_engine is None:
            raise ValueError("MATLAB engine instance is required")
        self.engine = matlab_engine
    
    def generate(self, config: WaveformConfig):
        """Generate waveform data based on configuration"""
        if config.modulation == "PAM":
            return self._generate_pam(config)
        elif config.modulation == "QAM":
            return self._generate_qam(config)
        elif config.modulation == "FSK":
            return self._generate_fsk(config)
        else:
            raise ValueError(f"Unknown modulation: {config.modulation}")
    
    def _generate_pam(self, config):
        """Call MATLAB pam_gui function"""
        result = self.engine.pam_gui(
            float(config.output_len),
            float(config.fs),
            float(config.Tsymb),
            float(config.fc),
            float(config.M),
            float(config.var),
            nargout=1
        )
        return np.array(result).flatten()
    
    def _generate_qam(self, config):
        """Call MATLAB mqam_gui function"""
        result = self.engine.mqam_gui(
            float(config.output_len),
            float(config.fs),
            float(config.Tsymb),
            float(config.fc),
            float(config.M),
            nargout=1
        )
        return np.array(result).flatten()
    
    def _generate_fsk(self, config):
        """Call MATLAB fsk_gui function"""
        if config.freq_sep is None:
            result = self.engine.fsk_gui(
                float(config.output_len),
                float(config.fs),
                float(config.Tsymb),
                float(config.fc),
                float(config.M),
                nargout=1
            )
        else:
            result = self.engine.fsk_gui(
                float(config.output_len),
                float(config.fs),
                float(config.Tsymb),
                float(config.fc),
                float(config.M),
                float(config.freq_sep),
                nargout=1
            )
        return np.array(result).flatten()


class Waveform:
    """Main waveform class"""
    
    def __init__(self, fs=None, Tsymb=None, Nsymb=None, fc=None, M=None, 
                 modulation=None, var=None, freq_sep=None, eng=None):
        """
        
        Usage:
            waveform = Waveform(fs=48e3, Tsymb=1e-3, Nsymb=2048, fc=20e3, 
                               M=16, modulation="PAM", var=1.0, eng=eng)
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
            freq_sep=freq_sep
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
                      f"fc{int(self.fc)}-Tsymb{self.Tsymb}")
        return config_name.replace('.', '_')
    
    @classmethod
    def from_json(cls, config_name, eng, rootpath='', 
                  datapath='gui/waveform_data', data_index=-1):
        """
        Load waveform from saved configuration
        
        Usage:
            waveform = Waveform.from_json(
                config_name="PAM-M16-fs48000-fc20000-Tsymb0_001",
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