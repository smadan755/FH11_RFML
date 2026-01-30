import json, os
import numpy as np
from specs import SignalSpec, ChannelSpec
from channel_effects import apply_channel
from mix import mix_signals

from signals.psk import generate_psk
from signals.qam import generate_qam
from signals.ofdm import generate_ofdm
from signals.gfsk import generate_gfsk
from signals.dsss_oqpsk import generate_dsss_oqpsk
from signals.css_lora import generate_css_lora

GEN_MAP = {
    "PSK": generate_psk,
    "QAM": generate_qam,
    "OFDM": generate_ofdm,
    "GFSK": generate_gfsk,
    "DSSS_OQPSK": generate_dsss_oqpsk,
    "CSS_LORA": generate_css_lora,
}

def generate_one(sample_id: int, fs: float, n: int, signal_specs, channel: ChannelSpec, mix_spec):
    waves = []
    for ss in signal_specs:
        w = GEN_MAP[ss.name](ss)
        waves.append(w)

    xs = [w.x for w in waves]
    y, mix_meta = mix_signals(xs, fs, mix_spec.freq_offsets_hz, mix_spec.gains)

    y = apply_channel(y, fs, channel.snr_db, channel.cfo_hz, channel.multipath_taps, seed=sample_id)

    meta = {
        "sample_id": sample_id,
        "fs": fs,
        "n": n,
        "signals": [w.meta for w in waves],
        "mix": mix_meta,
        "channel": {"snr_db": channel.snr_db, "cfo_hz": channel.cfo_hz,
                    "multipath_len": None if channel.multipath_taps is None else len(channel.multipath_taps)}
    }
    # label (coarse multi-label example)
    meta["label_multilabel"] = [w.meta["label"] for w in waves]

    return y.astype(np.complex64), meta, waves

def save_npz(out_dir: str, sample_id: int, x: np.ndarray, meta: dict):
    os.makedirs(out_dir, exist_ok=True)
    np.savez_compressed(os.path.join(out_dir, f"{sample_id:08d}.npz"), x=x)
    with open(os.path.join(out_dir, f"{sample_id:08d}.json"), "w") as f:
        json.dump(meta, f, indent=2)
