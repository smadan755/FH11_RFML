from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class SignalSpec:
    name: str               # "BPSK", "QPSK", "QAM", "GFSK", "OFDM", ...
    fs: float               # sampling rate (Hz)
    n: int                  # samples per example
    seed: int = 0
    params: Dict[str, Any] = None  # per-signal parameters

@dataclass
class ChannelSpec:
    snr_db: float = 10.0
    cfo_hz: float = 0.0
    multipath_taps: Optional[np.ndarray] = None  # complex FIR taps

@dataclass
class MixSpec:
    k: int = 1                          # number of signals in mixture
    freq_offsets_hz: Optional[List[float]] = None # per-signal freq placement
    gains: Optional[List[float]] = None          # per-signal amplitude scaling

@dataclass
class Waveform:
    x: np.ndarray              # complex baseband, shape (n,)
    bits: Optional[np.ndarray] # optional
    meta: Dict[str, Any]       # must include label info
