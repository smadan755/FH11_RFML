# FH11_RFML – README_update0129_EN.md (2026-01-29)

**Purpose:** This repo supports an end-to-end pipeline for **RF waveform dataset generation → optional mixed-signal overlap (k-mix) + channel impairments → PyTorch training/evaluation for coarse-family classification**.

---

TL;DR:
What you only need to run:
- gen_single.py // for one signal
- gen_large.py // (optional) to generate large dataset
- train_resnet1d.py //train model
- eval_confusion.py //run best_model.py and get confusion matrix
- performance output + best_model.py will automatically save into `runs` folder

Every RF signal code should go under `signals` folder
- there is README.md file under this folder if you are interested.

You do *not* need to run below files:
- channel_effects.py is adding noise + normalizing the signal.
- specs.py is defining what "specs" we should focus.
- dataset_orchestration.py just integrates diff signals and save it with metafile format (.npz + .jason)
- mix.py just mix multiple coarse families (#k)
- visualizaion.py is helper function to visualize plots (no need to run)



- 


## 1) Repository structure

### Top-level (current)
```
FH11_RFML/
  model/
    resnet1d/
      runs/                       # training outputs (best.pt, confusion png, logs)
      train_resnet1d.py           # 1D ResNet (I/Q) multi-label training
      eval_confusion.py           # per-class (2x2) confusion evaluation for multi-label
  out_dataset/                    # generated dataset (.npz + .json)
  signals/                        # (optional) signal generation code / docs (project-specific)
  sionna/                         # (optional) channel / Sionna-RT experiments
  tools/                          # utilities
  matlab_testing_ground/          # MATLAB waveform prototyping (if present)
  gui/                            # GUI work (if present)
  requirements.txt
  README.md
```

### `out_dataset/` format (expected)
For each sample id `00000042`:
- `out_dataset/00000042.npz` contains:
  - `x`: complex baseband I/Q (shape `(n,)`, dtype complex)
  - *(optional)* `bits0`, `bits1`, ... if you save per-signal bits (not required for training)
- `out_dataset/00000042.json` contains metadata, including one of:
  - `label_multilabel`: list of coarse labels, e.g. `["OFDM", "GFSK"]`
  - OR `signals`: list of dicts where each has `"label": "OFDM"` etc.

---

## 2) Coarse families (labels)

We train **multi-label** classification over 6 coarse families:

```
["PSK", "QAM", "GFSK", "OFDM", "DSSS_OQPSK", "CSS_LORA"]
```

**Why multi-label?**  
Because the dataset contains both k=1 and k>=2 mixtures, multi-label handles both:
- k=1 → one-hot label vector
- k=2 → two-hot label vector
- …etc.

---

## 3) How to run (Windows / PowerShell)

### 3.1 Dataset generation
- For single generation, use: `gen_single.py` 

- For "large" dataset generation, use: `gen_large.py`

Run it from the repo root:

```powershell
cd C:\User\Desktop\FH11_RFML
python scripts\gen_large.py --out_dir out_dataset --num_samples 2000 --k_min 1 --k_max 2
```

Common knobs (typical):
- `--fs 10e6` and `--n 4096`
- `--snr_min -10 --snr_max 20`
- `--cfo_frac 0.001` (start smaller; increase later)
- `--multipath` (enable multipath FIR)

> If your generation script lives elsewhere, adapt the path accordingly. The key output is `out_dataset/*.npz` + `*.json`.

---

### 3.2 Train: 1D ResNet (raw I/Q)
From the repo root:

```powershell
python model\resnet1d\train_resnet1d.py --data_dir out_dataset --epochs 25 --batch_size 64 --use_pos_weight
```

What it does:
- Loads `x` from `.npz`, converts to a 2-channel `(I,Q)` tensor of shape `(2, n)`
- Uses **BCEWithLogitsLoss** (multi-label); optional `pos_weight` to handle class imbalance
- Saves a checkpoint (recommended path): `model/resnet1d/runs/best_resnet1d.pt`

Recommended edits (if not already applied):
- In `train_resnet1d.py`, set:
  - `best_path = os.path.join("model","resnet1d","runs","best_resnet1d.pt")`
- Use GPU-friendly transfers inside the epoch loop:
  - `X = X.to(device, non_blocking=True)` and `y = y.to(device, non_blocking=True)`

---

### 3.3 Evaluate: per-class confusion (multi-label)
From the repo root:

```powershell
python model\resnet1d\eval_confusion.py ^
--data_dir out_dataset ^
  --ckpt_path model\resnet1d\runs\best_resnet1d.pt ^
  --out_dir model\resnet1d\runs ^
  --thresh 0.5
```

Outputs:
- `confusion_per_class.npy` (shape `(C,2,2)`)
- `confusion_per_class.png` (grid plot)

**Interpretation:**  
In multi-label, each class is a binary detector (present/absent) → you get **one 2×2 confusion matrix per class**:
- TP: present & predicted present
- FN: present but missed
- FP: absent but predicted present (false alarm)
- TN: absent & predicted absent

⚠️ Small dataset note:
- If you only generated ~20 samples and your eval script uses “last 10% as test”, you will evaluate on ~2 samples, so counts will look like 0/1/2.
- Use all samples for quick sanity checks, or increase dataset size (thousands+) for meaningful metrics.

---

## 4) Common path/import issues (Windows)

### 4.1 “No module named …” when using `-m`
- `python -m something` requires `something` to be importable as a module path.
- If your script is at `model/resnet1d/train_resnet1d.py`, the module path is:
  - `python -m model.resnet1d.train_resnet1d`
- This requires:
  - `model/__init__.py`
  - `model/resnet1d/__init__.py`  
  (empty files are fine)

### 4.2 Recommended: run by file path (simplest)
- Training: `python model\resnet1d\train_resnet1d.py ...`
- Eval: `python model\resnet1d\eval_confusion.py ...`

### 4.3 Eval importing Train code
If `eval_confusion.py` imports from `train_resnet1d.py`, ensure:
- `from train_resnet1d import ResNet1D, RFMixedDataset, CLASSES`
- If imports still fail, add at the top of `eval_confusion.py`:
```python
import os, sys
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)
```

---

## 5) Model/metric notes (recommended practice)

### 5.1 Multi-label loss
- Use `BCEWithLogitsLoss` for k-mix (k=1..K).
- Use `pos_weight` if class presence is imbalanced.

### 5.2 Thresholding
- Default `thresh=0.5` is OK to start.
- For better metrics, sweep thresholds on validation and pick the best macro-F1.

### 5.3 Suggested evaluation extras
- Per-class Precision/Recall/F1 from TP/FP/FN
- k-specific evaluation (k=1 vs k=2 vs k=3…) by grouping samples using metadata

---

## 6) Quick checklist

- [ ] `out_dataset/` contains paired `.npz` + `.json` files  
- [ ] `best_path` in training saves into `model/resnet1d/runs/`  
- [ ] `--ckpt_path` points to the real checkpoint  
- [ ] Increase dataset size (thousands+) for meaningful confusion/metrics  

---

## 7) Notes
- Neet to improve 1D ResNet model for better performance
- Need to test spectogram + 2D CNN
- Need to test 2D I/Q data + Transformer 
