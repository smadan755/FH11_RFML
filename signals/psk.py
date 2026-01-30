import numpy as np
from specs import SignalSpec, Waveform
from channel_effects import normalize_power

def generate_psk(spec: SignalSpec) -> Waveform:
    p = spec.params or {}
    mode = p.get("mode", "BPSK")        # "BPSK" or "QPSK"
    sps  = int(p.get("sps", 4))         # samples per symbol
    n_syms = int(np.ceil(spec.n / sps))
    rng = np.random.default_rng(spec.seed)

    bits = rng.integers(0, 2, size=(n_syms * (1 if mode=="BPSK" else 2),), dtype=np.int8)

    if mode == "BPSK":
        syms = 2*bits.astype(np.float32) - 1.0
        syms = syms.astype(np.complex64)
    else:
        b0 = bits[0::2]; b1 = bits[1::2]
        I = 2*b0.astype(np.float32) - 1.0
        Q = 2*b1.astype(np.float32) - 1.0
        syms = (I + 1j*Q) / np.sqrt(2)

    # simple rectangular pulse shaping (MVP). later replace with RRC filter.
    x = np.repeat(syms, sps)[:spec.n]
    x = normalize_power(x)

    return Waveform(
        x=x,
        bits=bits,
        meta={"label": "PSK", "subtype": mode, "sps": sps}
    )
