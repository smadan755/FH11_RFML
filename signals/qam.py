import numpy as np
from specs import SignalSpec, Waveform
from channel_effects import normalize_power

def _square_qam_constellation(M: int):
    m = int(np.sqrt(M))
    assert m*m == M, "M must be square (16, 64, ...)"
    levels = np.arange(-(m-1), m, 2, dtype=np.float32)
    xv, yv = np.meshgrid(levels, levels)
    const = (xv + 1j*yv).reshape(-1)
    const = const / np.sqrt(np.mean(np.abs(const)**2))  # unit avg power
    return const

def generate_qam(spec: SignalSpec) -> Waveform:
    p = spec.params or {}
    M   = int(p.get("M", 16))
    sps = int(p.get("sps", 4))
    rng = np.random.default_rng(spec.seed)

    k = int(np.log2(M))
    n_syms = int(np.ceil(spec.n / sps))
    bits = rng.integers(0, 2, size=(n_syms*k,), dtype=np.int8)

    const = _square_qam_constellation(M)
    # pack bits -> symbol index (simple binary; upgrade to Gray later if you want)
    idx = np.zeros(n_syms, dtype=np.int32)
    for i in range(k):
        idx += (bits[i::k].astype(np.int32) << (k-1-i))
    syms = const[idx]

    x = np.repeat(syms, sps)[:spec.n]
    x = normalize_power(x)

    return Waveform(
        x=x,
        bits=bits,
        meta={"label": "QAM", "M": M, "sps": sps}
    )
