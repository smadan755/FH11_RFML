
'''
This file is for large dataset generation with random mixtures.

saved format
  - `out_dir/00000000.npz`: `x` + `bits0/bits1/...`(if available)
  - `out_dir/00000000.json`: meta(label, params, channel info, mixed etc)
  
  '''

# how to run?
'''
python gen_large.py --out_dir out_dataset --num_samples 2000 --k_min 1 --k_max 2

# other paramters you can adjust (default):
--fs 10e6
--n 4096
--families PSK,QAM,GFSK,OFDM,DSSS_OQPSK,CSS_LORA
--snr_min -10.0
--snr_max 20.0
--cfo_frac 0.005
--multipath
--print_every 100

'''
# gen_large.py
import os
import json
import argparse
from dataclasses import asdict
from typing import List, Tuple, Optional

import numpy as np

from specs import SignalSpec, ChannelSpec, MixSpec
from dataset_orchestration import generate_one  # uses GEN_MAP inside rfml/dataset.py


# ----------------------------
# Sampling helpers (dataset-level)
# ----------------------------

def sample_family(rng: np.random.Generator, families: List[str]) -> str:
    return rng.choice(families)

def sample_snr_db(rng: np.random.Generator, snr_min: float, snr_max: float) -> float:
    # uniform in dB is fine for MVP; you can also do bucketed sampling
    return float(rng.uniform(snr_min, snr_max))

def sample_cfo_hz(rng: np.random.Generator, fs: float, cfo_frac: float) -> float:
    # CFO in +/- (cfo_frac * fs)
    return float(rng.uniform(-cfo_frac * fs, cfo_frac * fs))

def maybe_sample_multipath(rng: np.random.Generator, enable: bool, max_taps: int = 5) -> Optional[np.ndarray]:
    if not enable:
        return None
    L = int(rng.integers(2, max_taps + 1))
    # exponential-ish power delay profile
    powers = np.exp(-np.linspace(0, 1.5, L))
    phases = rng.uniform(0, 2*np.pi, size=L)
    taps = np.sqrt(powers) * np.exp(1j * phases)
    taps = taps / np.linalg.norm(taps)
    return taps.astype(np.complex64)


# ----------------------------
# SignalSpec samplers per family
# ----------------------------

def sample_spec_psk(rng: np.random.Generator, fs: float, n: int, seed: int) -> SignalSpec:
    mode = rng.choice(["BPSK", "QPSK"])
    sps = int(rng.choice([4, 8]))
    return SignalSpec(
        name="PSK", fs=fs, n=n, seed=seed,
        params={"mode": mode, "sps": sps}
    )

def sample_spec_qam(rng: np.random.Generator, fs: float, n: int, seed: int) -> SignalSpec:
    M = int(rng.choice([16, 64]))
    sps = int(rng.choice([4, 8]))
    return SignalSpec(
        name="QAM", fs=fs, n=n, seed=seed,
        params={"M": M, "sps": sps}
    )

def sample_spec_gfsk(rng: np.random.Generator, fs: float, n: int, seed: int) -> SignalSpec:
    # choose rs and snap sps accordingly inside generator
    rs = float(rng.choice([0.5e6, 1e6, 2e6]))
    bt = float(rng.choice([0.3, 0.5, 0.7]))
    # dev_hz ~ [0.15..0.5] * rs
    dev_hz = float(rng.uniform(0.15 * rs, 0.5 * rs))
    return SignalSpec(
        name="GFSK", fs=fs, n=n, seed=seed,
        params={"rs": rs, "bt": bt, "dev_hz": dev_hz, "span_symbols": 4}
    )

def sample_spec_ofdm(rng: np.random.Generator, fs: float, n: int, seed: int) -> SignalSpec:
    nfft = int(rng.choice([64, 128]))
    ncp = int(nfft // rng.choice([4, 8]))  # nfft/4 or nfft/8
    if nfft == 64:
        nused = int(rng.choice([48]))      # keep simple
    else:
        nused = int(rng.choice([72, 96]))  # simple options
    mod = rng.choice(["QPSK", "16QAM"])
    return SignalSpec(
        name="OFDM", fs=fs, n=n, seed=seed,
        params={"nfft": nfft, "ncp": ncp, "nused": nused, "mod": mod}
    )

def sample_spec_dsss_oqpsk(rng: np.random.Generator, fs: float, n: int, seed: int) -> SignalSpec:
    chips_per_symbol = int(rng.choice([8, 16, 32]))
    sps_chip = int(rng.choice([2, 4]))
    use_half_sine = True
    return SignalSpec(
        name="DSSS_OQPSK", fs=fs, n=n, seed=seed,
        params={
            "chips_per_symbol": chips_per_symbol,
            "sps_chip": sps_chip,
            "use_half_sine": use_half_sine,
            "pn_seed": seed + 123
        }
    )

def sample_spec_css_lora(rng: np.random.Generator, fs: float, n: int, seed: int) -> SignalSpec:
    sf = int(rng.choice([7, 8, 9, 10, 11, 12]))
    bw = float(rng.choice([125e3, 250e3, 500e3]))
    preamble_len = int(rng.choice([8, 10]))
    return SignalSpec(
        name="CSS_LORA", fs=fs, n=n, seed=seed,
        params={"sf": sf, "bw": bw, "preamble_len": preamble_len}
    )

SPEC_SAMPLERS = {
    "PSK": sample_spec_psk,
    "QAM": sample_spec_qam,
    "GFSK": sample_spec_gfsk,
    "OFDM": sample_spec_ofdm,
    "DSSS_OQPSK": sample_spec_dsss_oqpsk,
    "CSS_LORA": sample_spec_css_lora,
}


# ----------------------------
# Bandwidth rough estimates for placement (Hz)
# (MVP heuristics for freq_offsets_hz)
# ----------------------------

def estimate_occupied_bw(spec: SignalSpec) -> float:
    p = spec.params or {}
    name = spec.name

    if name == "PSK" or name == "QAM":
        # approximate: Rs ~ fs/sps; roll-off ignored in MVP
        sps = float(p.get("sps", 4))
        rs = spec.fs / sps
        return 1.2 * rs  # simple factor

    if name == "GFSK":
        rs = float(p.get("rs", 1e6))
        dev = float(p.get("dev_hz", 0.25 * rs))
        # Carson-ish heuristic for FSK: ~2*(dev + Rs/2)
        return 2.0 * (dev + 0.5 * rs)

    if name == "OFDM":
        nfft = int(p.get("nfft", 64))
        nused = int(p.get("nused", 48))
        # assume subcarrier spacing ~ fs/nfft (generic)
        delta_f = spec.fs / nfft
        return 1.2 * nused * delta_f

    if name == "DSSS_OQPSK":
        sps_chip = float(p.get("sps_chip", 4))
        chip_rate = spec.fs / sps_chip
        return 1.2 * chip_rate

    if name == "CSS_LORA":
        bw = float(p.get("bw", 125e3))
        return 1.2 * bw

    return 0.2 * spec.fs


def choose_freq_offsets(
    rng: np.random.Generator,
    fs: float,
    specs: List[SignalSpec],
    guard_hz: float = 100e3
) -> List[float]:
    """
    Place K signals in the same baseband "window" by choosing frequency offsets.
    Greedy placement with rough BW estimation.
    """
    K = len(specs)
    if K == 1:
        return [0.0]

    bws = [estimate_occupied_bw(s) for s in specs]
    # available band within Nyquist: [-fs/2, fs/2]
    # we keep some margin so signals don't alias badly
    margin = 0.1 * fs
    lo = -fs/2 + margin
    hi =  fs/2 - margin

    placed = []
    for i in range(K):
        bw_i = bws[i]
        # try a few random candidates
        ok = False
        for _ in range(50):
            cand = float(rng.uniform(lo, hi))
            # ensure separation from previous placements
            good = True
            for (f_prev, bw_prev) in placed:
                if abs(cand - f_prev) < 0.5*(bw_i + bw_prev) + guard_hz:
                    good = False
                    break
            if good:
                placed.append((cand, bw_i))
                ok = True
                break
        if not ok:
            # fallback: place at 0 if stuck
            placed.append((0.0, bw_i))

    return [f for f, _ in placed]


def choose_gains(rng: np.random.Generator, k: int) -> List[float]:
    # random relative amplitudes (avoid extreme imbalance)
    gains = rng.uniform(0.6, 1.0, size=(k,)).tolist()
    return [float(g) for g in gains]


# ----------------------------
# Save utilities (x + bits + json meta)
# ----------------------------

def save_example(out_dir: str, sample_id: int, x: np.ndarray, meta: dict, waves_bits: List[Optional[np.ndarray]]):
    os.makedirs(out_dir, exist_ok=True)
    npz_path = os.path.join(out_dir, f"{sample_id:08d}.npz")
    json_path = os.path.join(out_dir, f"{sample_id:08d}.json")

    # store x and per-signal bits if present
    payload = {"x": x}
    for i, b in enumerate(waves_bits):
        if b is not None:
            payload[f"bits{i}"] = b
    np.savez_compressed(npz_path, **payload)

    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)


# ----------------------------
# Main generation loop
# ----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=str, default="out_dataset")
    ap.add_argument("--num_samples", type=int, default=2000) # WAS 2000
    ap.add_argument("--seed", type=int, default=0)

    ap.add_argument("--fs", type=float, default=10e6)
    ap.add_argument("--n", type=int, default=4096)

    #number of signals in mixture
    ap.add_argument("--k_min", type=int, default=1)
    ap.add_argument("--k_max", type=int, default=2)

    ap.add_argument("--families", type=str, default="PSK,QAM,GFSK,OFDM,DSSS_OQPSK,CSS_LORA")

    ap.add_argument("--snr_min", type=float, default=-10.0)
    ap.add_argument("--snr_max", type=float, default=20.0)
    ap.add_argument("--cfo_frac", type=float, default=0.005)  # CFO in +/- cfo_frac*fs

    ap.add_argument("--multipath", action="store_true")
    ap.add_argument("--print_every", type=int, default=100) # WAS 200

    args = ap.parse_args()

    out_dir = args.out_dir
    fs = float(args.fs)
    n = int(args.n)

    families = [f.strip() for f in args.families.split(",") if f.strip()]
    for f in families:
        if f not in SPEC_SAMPLERS:
            raise ValueError(f"Unknown family in --families: {f}. Known: {list(SPEC_SAMPLERS.keys())}")

    rng = np.random.default_rng(args.seed)

    # dataset-level loop
    for sample_id in range(args.num_samples):
        # mixture size
        k = int(rng.integers(args.k_min, args.k_max + 1))
        # choose families (allow duplicates? usually no; we avoid duplicates by default)
        chosen = rng.choice(families, size=k, replace=False).tolist()

        # build SignalSpecs
        signal_specs: List[SignalSpec] = []
        for idx, fam in enumerate(chosen):
            fam_seed = int(rng.integers(0, 2**31-1))
            spec = SPEC_SAMPLERS[fam](rng, fs, n, fam_seed)
            signal_specs.append(spec)

        # channel
        snr_db = sample_snr_db(rng, args.snr_min, args.snr_max)
        cfo_hz = sample_cfo_hz(rng, fs, args.cfo_frac)
        taps = maybe_sample_multipath(rng, args.multipath)
        channel = ChannelSpec(snr_db=snr_db, cfo_hz=cfo_hz, multipath_taps=taps)

        # mixing placement
        freq_offsets = choose_freq_offsets(rng, fs, signal_specs)
        gains = choose_gains(rng, k)
        mix = MixSpec(k=k, freq_offsets_hz=freq_offsets, gains=gains)

        # generate sample
        x, meta, waves = generate_one(
            sample_id=sample_id,
            fs=fs,
            n=n,
            signal_specs=signal_specs,
            channel=channel,
            mix_spec=mix,
        )

        # collect per-signal bits for saving
        # NOTE: generate_one currently returns only x, meta; bits are inside meta["signals"]? (not in our current design)
        # So we store "bits" by re-generating bits? Not ideal.
        # Better: modify rfml/dataset.py to also return the Waveform objects.
        #
        # Quick workaround: store bits if your generate_one meta includes them.
        # If not, just save none. (Recommended fix below.)
        waves_bits = [w.bits for w in waves]
        for s in signal_specs:
            # We cannot access Waveform.bits here unless generate_one returns them.
            waves_bits.append(None)

        # save
        save_example(out_dir, sample_id, x, meta, waves_bits)

        if args.print_every > 0 and (sample_id + 1) % args.print_every == 0:
            print(f"[{sample_id+1}/{args.num_samples}] saved to {out_dir}")

    print(f"Done. Dataset saved to: {out_dir}")


if __name__ == "__main__":
    main()
