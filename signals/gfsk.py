# rfml/signals/gfsk.py
import numpy as np
from specs import SignalSpec, Waveform
from channel_effects import normalize_power


# SignalSpec(name="GFSK", fs=10e6, n=4096, seed=1, params={"sps": 4, "bt": 0.5, "dev_hz": 250e3})


def _gaussian_impulse_response(bt: float, sps: int, span_symbols: int = 4) -> np.ndarray:
    """
    Simple Gaussian filter for GFSK.
    bt: bandwidth-time product (typical 0.3~0.7)
    sps: samples per symbol
    span_symbols: filter span in symbols
    """
    # time axis in symbol durations
    n = np.arange(-span_symbols*sps, span_symbols*sps + 1)
    t = n / sps  # in symbol units
    # Common approximation: sigma = sqrt(ln2) / (2*pi*BT)
    sigma = np.sqrt(np.log(2)) / (2 * np.pi * bt + 1e-12)
    h = np.exp(-0.5 * (t / sigma) ** 2)
    h = h / np.sum(h)
    return h.astype(np.float32)



def generate_gfsk(spec: SignalSpec) -> Waveform:
    """
    Params (spec.params):
      - sps: samples per symbol (int, default 4)
      - rs: symbol rate (float, optional). If provided, sps is overridden by round(fs/rs).
      - dev_hz: frequency deviation (float, default 0.25*rs)
      - bt: Gaussian BT (float). If None, does plain FSK (rectangular)
      - n_bits: number of bits (optional). If not provided, computed to fill n samples.
      - span_symbols: Gaussian filter span (default 4)
    """
    p = spec.params or {}
    fs = float(spec.fs)

    # decide sps / rs
    if "rs" in p:
        rs = float(p["rs"])
        sps = int(max(2, round(fs / rs)))
        rs = fs / sps  # snap to integer sps
    else:
        sps = int(p.get("sps", 4))
        rs = fs / sps

    bt = p.get("bt", 0.5)  # if None -> plain FSK
    span_symbols = int(p.get("span_symbols", 4))

    dev_hz = float(p.get("dev_hz", 0.25 * rs))

    rng = np.random.default_rng(spec.seed)

    # how many bits needed to fill spec.n
    n_bits = int(p.get("n_bits", int(np.ceil(spec.n / sps))))
    bits = rng.integers(0, 2, size=(n_bits,), dtype=np.int8)
    nrz = (2 * bits.astype(np.float32) - 1.0)  # {0,1} -> {-1,+1}

    # upsample NRZ to sample-rate
    m = np.repeat(nrz, sps)

    # apply Gaussian filter for GFSK if bt is not None
    if bt is not None:
        h = _gaussian_impulse_response(float(bt), sps, span_symbols=span_symbols)
        m = np.convolve(m, h, mode="same")

    # truncate/pad to exact length n
    if len(m) < spec.n:
        m = np.pad(m, (0, spec.n - len(m)))
    else:
        m = m[:spec.n]

    # instantaneous frequency deviation: f_inst = dev_hz * m(t)
    # phase increment per sample = 2*pi*f_inst/fs
    phase = np.cumsum(2 * np.pi * dev_hz * m / fs).astype(np.float32)

    x = np.exp(1j * phase).astype(np.complex64)
    x = normalize_power(x)

    meta = {
        "label": "GFSK" if bt is not None else "FSK",
        "rs": rs,
        "sps": sps,
        "dev_hz": dev_hz,
        "bt": bt,
        "span_symbols": span_symbols,
    }

    return Waveform(x=x, bits=bits, meta=meta)
