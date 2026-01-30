# rfml/signals/dsss_oqpsk.py
# this is not necessarily same with standard 802.15.4 
# but simlar to zigbee compliant, just a simple DSSS OQPSK generator
# just for coarse familty labeling purpose

import numpy as np
from specs import SignalSpec, Waveform
from channel_effects import normalize_power

# ex) SignalSpec(name="DSSS_OQPSK", fs=10e6, n=4096, seed=2, params={"chips_per_symbol": 16, "sps_chip": 4, "use_half_sine": True})

def _half_sine_pulse(sps_chip: int) -> np.ndarray:
    # half-sine shaping over one chip duration
    n = np.arange(sps_chip)
    pulse = np.sin(np.pi * (n + 0.5) / sps_chip)
    pulse = pulse / np.sum(pulse)
    return pulse.astype(np.float32)


def generate_dsss_oqpsk(spec: SignalSpec) -> Waveform:
    """
    Params (spec.params):
      - chips_per_symbol: spreading factor (int, default 16)
      - sps_chip: samples per chip (int, default 4)
      - pn_seed: seed for PN sequence (int, default spec.seed+123)
      - use_half_sine: bool (default True)
      - n_bits: optional, number of bits to generate
    """
    p = spec.params or {}
    fs = float(spec.fs)

    chips_per_symbol = int(p.get("chips_per_symbol", 16))
    sps_chip = int(p.get("sps_chip", 4))
    use_half_sine = bool(p.get("use_half_sine", True))

    rng = np.random.default_rng(spec.seed)
    pn_rng = np.random.default_rng(int(p.get("pn_seed", spec.seed + 123)))

    # OQPSK: split bits into I and Q streams
    # Need enough chips to fill n samples
    chips_needed = int(np.ceil(spec.n / sps_chip)) + chips_per_symbol  # margin
    # Each bit becomes chips_per_symbol chips after spreading, and I/Q alternate bits
    bits_needed = int(np.ceil(chips_needed / chips_per_symbol)) * 2

    n_bits = int(p.get("n_bits", bits_needed))
    bits = rng.integers(0, 2, size=(n_bits,), dtype=np.int8)

    i_bits = bits[0::2]
    q_bits = bits[1::2]

    # map bits to NRZ {-1,+1}
    i_sym = (2 * i_bits.astype(np.float32) - 1.0)
    q_sym = (2 * q_bits.astype(np.float32) - 1.0)

    # PN code for spreading: length chips_per_symbol, values {-1,+1}
    pn = pn_rng.integers(0, 2, size=(chips_per_symbol,), dtype=np.int8)
    pn = (2 * pn.astype(np.float32) - 1.0)

    # spread: each symbol expands to chips_per_symbol chips
    i_chips = np.concatenate([s * pn for s in i_sym]).astype(np.float32)
    q_chips = np.concatenate([s * pn for s in q_sym]).astype(np.float32)

    # upsample chips to samples
    i_samples = np.repeat(i_chips, sps_chip)
    q_samples = np.repeat(q_chips, sps_chip)

    # OQPSK offset: delay Q by half-chip
    half = sps_chip // 2
    if half > 0:
        q_samples = np.r_[np.zeros(half, dtype=np.float32), q_samples]
        i_samples = np.r_[i_samples, np.zeros(half, dtype=np.float32)]

    # optional half-sine pulse shaping (gives Zigbee-ish smoothness)
    if use_half_sine:
        pulse = _half_sine_pulse(sps_chip)
        i_samples = np.convolve(i_samples, pulse, mode="same")
        q_samples = np.convolve(q_samples, pulse, mode="same")

    # combine into complex baseband
    x = (i_samples + 1j * q_samples).astype(np.complex64)

    # truncate/pad to exact length
    if len(x) < spec.n:
        x = np.r_[x, np.zeros(spec.n - len(x), dtype=np.complex64)]
    else:
        x = x[:spec.n]

    x = normalize_power(x)

    # approximate effective rates (for metadata only)
    chip_rate = fs / sps_chip
    sym_rate = chip_rate / chips_per_symbol

    meta = {
        "label": "DSSS_OQPSK",
        "chips_per_symbol": chips_per_symbol,
        "sps_chip": sps_chip,
        "chip_rate": chip_rate,
        "sym_rate": sym_rate,
        "use_half_sine": use_half_sine,
    }

    return Waveform(x=x, bits=bits, meta=meta)
