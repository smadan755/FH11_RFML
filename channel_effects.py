import numpy as np

## This file is about channel effects (normalization+applying noise to signals)

# you need to normalize the power of the signal before applying channel effects
def normalize_power(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    p = np.mean(np.abs(x)**2)
    return x / np.sqrt(p + eps)

# Carrier Frequency Offset - noise 1
# frequency mismatch between transmitter/receiver oscillators and the Doppler effect caused by movement.
def apply_cfo(x: np.ndarray, fs: float, cfo_hz: float) -> np.ndarray:
    if cfo_hz == 0:
        return x
    n = np.arange(len(x))
    rot = np.exp(1j * 2*np.pi * cfo_hz * n / fs)
    return x * rot

# Multipath - noise 2
# caused by the signal reaching the receiving antenna by two or more paths.
def apply_multipath(x: np.ndarray, taps: np.ndarray) -> np.ndarray:
    # taps: complex FIR taps (e.g., length 3~7)
    if taps is None:
        return x
    return np.convolve(x, taps, mode="same")

# Additive White Gaussian Noise - noise 3
def apply_awgn(x: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    # assumes x is already normalized (unit power)
    snr_lin = 10**(snr_db/10.0)
    noise_var = 1.0 / snr_lin
    w = (rng.normal(0, np.sqrt(noise_var/2), size=x.shape) +
         1j*rng.normal(0, np.sqrt(noise_var/2), size=x.shape))
    return x + w

# Complete channel model (abpply all above)
def apply_channel(x: np.ndarray, fs: float, snr_db: float, cfo_hz: float = 0.0, taps=None, seed: int = 0):
    rng = np.random.default_rng(seed)
    x = normalize_power(x)
    x = apply_multipath(x, taps)
    x = apply_cfo(x, fs, cfo_hz)
    x = normalize_power(x)
    x = apply_awgn(x, snr_db, rng)
    return x
