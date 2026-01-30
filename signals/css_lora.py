# rfml/signals/css_lora.py
import numpy as np
from specs import SignalSpec, Waveform
from channel_effects import normalize_power


def _upchirp(fs: float, bw: float, Ts: float, phi0: float = 0.0) -> np.ndarray:
    """
    Generate a complex baseband upchirp that sweeps from -bw/2 to +bw/2 over Ts.
    phase(t) = 2π( -bw/2 * t + (bw/(2Ts)) * t^2 ) + phi0
    """
    n = int(round(fs * Ts))
    t = np.arange(n) / fs
    phase = 2 * np.pi * (-bw/2 * t + (bw/(2*Ts)) * t**2) + phi0
    return np.exp(1j * phase).astype(np.complex64)

# ex) SignalSpec(name="CSS_LORA", fs=10e6, n=4096, seed=3, params={"sf": 9, "bw": 125e3, "preamble_len": 8})

def generate_css_lora(spec: SignalSpec) -> Waveform:
    """
    Params (spec.params):
      - sf: spreading factor (int, default 9)
      - bw: bandwidth in Hz (float, default 125e3)
      - preamble_len: number of preamble symbols (int, default 8)
      - n_symbols: optional, payload symbols count. If not provided, computed to fill n.
    """
    p = spec.params or {}
    fs = float(spec.fs)

    sf = int(p.get("sf", 9))
    bw = float(p.get("bw", 125e3))
    preamble_len = int(p.get("preamble_len", 8))

    M = 2**sf  # number of chirp bins
    # LoRa symbol duration (approx): Ts = M / BW
    Ts = M / bw

    rng = np.random.default_rng(spec.seed)

    # Base upchirp
    base = _upchirp(fs, bw, Ts)

    # How many total symbols needed to reach spec.n
    sym_len = len(base)
    n_total_syms = int(np.ceil(spec.n / sym_len))

    # build preamble + payload
    payload_syms = max(0, n_total_syms - preamble_len)
    payload_syms = int(p.get("n_symbols", payload_syms))

    # random symbol values 0..M-1 (these are not "bits" but LoRa symbol indices)
    symbols = rng.integers(0, M, size=(payload_syms,), dtype=np.int32)

    out = []
    # preamble: repeated upchirps
    for _ in range(preamble_len):
        out.append(base)

    # payload: shift chirp by symbol-dependent frequency offset
    # f_shift = (sym / M) * bw
    t = np.arange(sym_len) / fs
    for s in symbols:
        f_shift = (float(s) / M) * bw
        x = base * np.exp(1j * 2*np.pi * f_shift * t).astype(np.complex64)
        out.append(x)

    x = np.concatenate(out) if len(out) > 0 else base
    x = x[:spec.n] if len(x) >= spec.n else np.r_[x, np.zeros(spec.n - len(x), dtype=np.complex64)]
    x = normalize_power(x)

    meta = {
        "label": "CSS_LORA",
        "sf": sf,
        "bw": bw,
        "Ts": Ts,
        "preamble_len": preamble_len,
        "M": M,
    }

    # We store symbol indices rather than raw bits (fine for dataset/debug)
    return Waveform(x=x, bits=None, meta={**meta, "symbols": symbols.tolist()})
