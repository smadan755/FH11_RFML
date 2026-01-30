import numpy as np
from channel_effects import normalize_power

def place_in_band(x: np.ndarray, fs: float, f_off_hz: float):
    if f_off_hz == 0:
        return x
    n = np.arange(len(x))
    return x * np.exp(1j*2*np.pi*f_off_hz*n/fs)

def mix_signals(xs, fs: float, freq_offsets_hz=None, gains=None):
    k = len(xs)
    if freq_offsets_hz is None:
        freq_offsets_hz = [0.0]*k
    if gains is None:
        gains = [1.0]*k

    y = np.zeros_like(xs[0], dtype=np.complex64)
    metas = []
    for i in range(k):
        xi = place_in_band(xs[i], fs, freq_offsets_hz[i])
        y += gains[i] * xi
        metas.append({"f_off_hz": float(freq_offsets_hz[i]), "gain": float(gains[i])})

    y = normalize_power(y)
    return y, metas
