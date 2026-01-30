# FH11_RFML.signals - Coarse-family waveform generators

This folder contains per-family waveform generators for *coarse RF classification*.

**Goal:** generate realistic-enough baseband I/Q waveforms for **family-level** classification
under noise/impairments and (optionally) mixed-signal overlap.

Each module exposes:
- `generate_<family>(spec: SignalSpec) -> Waveform`

Where:
- `SignalSpec` defines the family name, sampling rate, sample length, seed, and parameters
- `Waveform` returns `x` (complex baseband), optional `bits`, and `meta` dict

---

## Common dataset assumptions (recommended MVP)

We generate fixed-length examples:

- Sampling rate: `fs = 10e6` (10 Msps)
- Example length: `n = 4096` (or 8192)
- Channel/impairments are applied *after* generation:
  - AWGN (SNR in dB)
  - CFO (Hz)
  - Optional multipath (FIR taps)

**Note**: We do NOT implement full protocol stacks (true Wi-Fi/LTE/NR framing).
Instead, we generate *family-typical* structures that are sufficient for coarse classification.

---

## 1) PSK (BPSK / QPSK) — `psk.py`

### What it is (coarse features)
- Constant-envelope-ish (after shaping) with constellation points on a circle/axes
- Strong phase-based structure

### Parameters (`SignalSpec.params`)
- `mode`: `"BPSK"` or `"QPSK"`
- `sps`: samples per symbol (integer). Typical: 4 or 8
- (optional later) RRC shaping: `beta` roll-off (if you add RRC)

### Recommended ranges for dataset sampling
- `mode`: {BPSK, QPSK}
- `sps`: {4, 8}

### SignalSpec example
```python
SignalSpec(
  name="PSK", fs=10e6, n=4096, seed=1,
  params={"mode":"QPSK","sps":4}
)
```

---


## 2) QAM (16 / 64QAM) — `qam.py`

### What it is (coarse features)

* Dense constellation with multiple amplitude levels
* Strong amplitude/phase structure (more fragile under low SNR than PSK)

### Parameters (`SignalSpec.params`)

* `M`: 16 or 64
* `sps`: samples per symbol (4 or 8)

### Recommended ranges

* `M`: {16, 64} (for coarse you may group both under "QAM")
* `sps`: {4, 8}

### SignalSpec example

```python
SignalSpec(
  name="QAM", fs=10e6, n=4096, seed=2,
  params={"M":16,"sps":4}
)
```

---

## 3) (G)FSK — `gfsk.py`

### What it is (coarse features)

* Frequency shift keyed: symbol changes affect instantaneous frequency
* Typically constant envelope: `x[n] = exp(j*phase[n])`
* Bluetooth-like signals are GFSK-like (not full Bluetooth framing)

### Parameters (`SignalSpec.params`)

* `rs`: symbol rate (Hz). If set, generator will choose `sps ~ fs/rs`
* `sps`: samples per symbol (alternative to `rs`)
* `dev_hz`: frequency deviation (Hz), controls “how far” frequency shifts
* `bt`: Gaussian BT (0.3–0.7 typical). If `None`, falls back to plain FSK
* `span_symbols`: Gaussian filter span in symbols (default 4)

### Recommended ranges

* `rs`: 0.5e6 to 2e6 (snap to integer sps)
* `bt`: {0.3, 0.5, 0.7}
* `dev_hz`: about 0.15*rs to 0.5*rs

### SignalSpec example

```python
SignalSpec(
  name="GFSK", fs=10e6, n=4096, seed=3,
  params={"rs":1e6,"bt":0.5,"dev_hz":250e3}
)
```

---

## 4) OFDM (generic OFDM family) — `ofdm.py`

### What it is (coarse features)

* Multi-carrier: many narrow subcarriers, IFFT + cyclic prefix
* OFDM “family” covers Wi-Fi/LTE/5G at coarse level (protocol specifics omitted)

### Parameters (`SignalSpec.params`)

* `nfft`: FFT size (64 or 128 recommended)
* `ncp`: cyclic prefix length (nfft/4 or nfft/8)
* `nused`: number of used subcarriers (e.g., 48 for nfft=64)
* `mod`: subcarrier modulation `"QPSK"` or `"16QAM"`

### Recommended ranges

* `nfft`: {64, 128}
* `ncp`: {nfft/4, nfft/8}
* `nused`: {48 (for 64), 72 or 96 (for 128)} (keep it simple)
* `mod`: {QPSK, 16QAM}

### SignalSpec example

```python
SignalSpec(
  name="OFDM", fs=10e6, n=4096, seed=4,
  params={"nfft":64,"ncp":16,"nused":48,"mod":"QPSK"}
)
```

---

## 5) DSSS/OQPSK (Zigbee-like) — `dsss_oqpsk.py`

### What it is (coarse features)

* Spread-spectrum: data is “spread” by fast chip sequence → wideband-ish
* OQPSK: Q branch delayed by half-chip → smoother phase trajectory

### Parameters (`SignalSpec.params`)

* `chips_per_symbol`: spreading factor (8–32 typical)
* `sps_chip`: samples per chip (2–8 typical; 4 is a good default)
* `pn_seed`: seed for PN code (optional)
* `use_half_sine`: apply half-sine pulse shaping (bool)

### Recommended ranges

* `chips_per_symbol`: {8, 16, 32}
* `sps_chip`: {2, 4}
* `use_half_sine`: {True}

### SignalSpec example

```python
SignalSpec(
  name="DSSS_OQPSK", fs=10e6, n=4096, seed=5,
  params={"chips_per_symbol":16,"sps_chip":4,"use_half_sine":True}
)
```

---

## 6) CSS (LoRa-like chirp spread spectrum) — `css_lora.py`

### What it is (coarse features)

* Chirp modulation: frequency sweeps over time
* Very distinctive diagonal chirp patterns in spectrogram

### Parameters (`SignalSpec.params`)

* `sf`: spreading factor (7–12)
* `bw`: bandwidth (Hz). Typical: 125k, 250k, 500k
* `preamble_len`: number of preamble chirps (6–10)

### Recommended ranges

* `sf`: {7, 8, 9, 10, 11, 12}
* `bw`: {125e3, 250e3, 500e3}
* `preamble_len`: {8, 10}

### SignalSpec example

```python
SignalSpec(
  name="CSS_LORA", fs=10e6, n=4096, seed=6,
  params={"sf":9,"bw":125e3,"preamble_len":8}
)
```


