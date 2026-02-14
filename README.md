# FH11_RFML

Project Repo for Faculty Honors team FH11: Spectrum Sensing and Signal Classification using Deep Neural Networks

## Overview

An end-to-end RF signal analysis and machine learning platform that combines MATLAB DSP waveform generation with PyTorch deep learning for automatic modulation classification. A tabbed PySide6 GUI walks through the full pipeline: generate waveforms, apply channel effects, train a classifier, run inference, and evaluate results.

### Supported Modulation Types

PAM, QAM, PSK, FSK, FHSS, OFDM, LFM, Barker, FMCW, WiFi, LTE, 5G\_NR

## Quick Start

### 1. Install dependencies

```powershell
pip install -r requirements.txt
pip install -r gui_alternate/requirements.txt
```

### 2. Install MATLAB Engine for Python

The engine version must match your MATLAB release. For example, with MATLAB R2025b:

```powershell
pip install --user "matlabengine==25.2.2"
```

### 3. Install npy-matlab (writeNPY/readNPY)

```powershell
cd C:\Users\madan\FH11_RFML
git clone https://github.com/kwikteam/npy-matlab.git
```

### 4. Run the GUI

```powershell
cd gui_alternate
python main_window.py
```

## GUI Tabs

The application is organized into five tabs that form a complete signal-to-classification pipeline:

### 1. Waveform Selection

Configure and generate RF waveforms via MATLAB. Parameters include sampling frequency, carrier frequency, symbol period, modulation order (M), pulse shaping (RRC/rectangular), and more. Four real-time plots show time-domain, frequency-domain, IQ constellation, and spectrogram views.

- **Save to Dataset** -- save individual waveforms as `.npy` files
- **Batch Generate** -- generate N samples per modulation class for ML training. Per-class M choices are exposed in a collapsible panel so you can control which modulation orders are randomly sampled.

### 2. Channel & Noise

Apply channel effects and noise to generated waveforms. Includes multi-path fading, AWGN, colored noise, and SNR controls with interactive spectrum visualization.

### 3. ML Training

Train PyTorch classifiers on your generated dataset.

**Exposed controls:**
- Model architecture: SimpleCNN, TinyConv, MLP, ResNet1DOptimized
- Epochs, batch size

**Training Hyperparameters** (collapsible):
- Learning rate (default 0.001)
- Weight decay (default 1e-4)
- Label smoothing (default 0.1)
- Validation split (default 0.2)
- Gradient clip (default 1.0)

**Model Hyperparameters** (collapsible, varies by model):
- ResNet1DOptimized: base filters (default 64), dropout (default 0.2)

Training uses AdamW with cosine annealing LR scheduling, warmup, mixed-precision (AMP), and gradient clipping. Loss and accuracy curves update in real time.

### 4. Inference Results

Load a trained model and run inference on test waveforms. Displays confusion matrix, classification report, and ROC curves with AUC.

### 5. Evaluate Model

Generate new waveforms and classify them with a loaded model for quick spot-checking.

Trained models are automatically forwarded from the ML Training tab to both the Inference and Evaluate tabs.

## Model Architectures

| Model | Input | Description |
|---|---|---|
| SimpleCNN | 1-ch signal | Two Conv1d layers + adaptive pooling + FC |
| TinyConv | 1-ch signal | Single Conv1d layer + adaptive pooling + FC |
| MLP | Flattened vector | Three fully-connected layers |
| ResNet1DOptimized | 2-ch IQ | Multi-scale input, 10 residual blocks with squeeze-excitation, GroupNorm, progressive filter scaling (64-256) |

Models are saved as `.pth` + `.json` metadata to `gui_alternate/models/`.

## Project Structure

```
FH11_RFML/
  gui_alternate/            # Main GUI application
    main_window.py          # Entry point
    gui_elements.py         # Waveform class (MATLAB bridge)
    tabs/                   # UI tabs
      waveform_tab.py       # Waveform generation & batch dataset creation
      channel_tab.py        # Channel & noise effects
      ml_training_tab.py    # Model training interface
      inference_tab.py      # Inference & evaluation visualizations
      evaluate_model_tab.py # Live model evaluation
    backend/                # Core services
      trainer.py            # TrainerThread (PyTorch training loop)
      torch_models.py       # Model definitions
      tf_models.py          # TensorFlow models (legacy)
      dataset_generator.py  # Batch waveform generation thread
      core.py               # WaveformConfig dataclass
      generators.py         # MATLAB waveform generator wrapper
      waveform_pipeline.py  # End-to-end generation pipeline
    widgets/                # Custom Qt widgets
      waveform_plots.py     # Time, freq, IQ, spectrogram plots
      training_chart.py     # Live loss/accuracy chart
      power_spectrum.py     # Power spectrum display
      noise_spectrum.py     # Noise spectrum display
      constellation.py      # IQ constellation plot
      toggle_switch.py      # Custom toggle switch
    styles/
      stylesheet.py         # Dark theme
    waveform_functions/     # MATLAB .m files that return data to Python
  gui/                      # Legacy GUI (deprecated, kept for reference)
  sionna/                   # Sionna channel simulation experiments
  tools/SRD/                # Software Receiver Design reference code
  *.m                       # Root MATLAB generators (save to disk)
  data_bpsk/, data_pam/     # Example generated data
```

## Dependencies

**Core:**
- PySide6, NumPy, SciPy, Matplotlib, python-dotenv
- MATLAB Engine for Python (must match your MATLAB release)
- npy-matlab (for MATLAB `.npy` I/O)

**ML:**
- PyTorch, scikit-learn

## Environment Setup

Copy `.env.example` to `.env` and set the `ROOT` variable to your local repo path.

## Troubleshooting

- **"Too many output arguments"** -- call MATLAB functions with `nargout=0` when they don't return values. The `gui/waveform_functions/` versions return data; root `.m` files save to disk.
- **"Undefined function 'writeNPY'"** -- clone `npy-matlab` and add it to the MATLAB path.
- **MATLAB Engine version mismatch** -- the pip package version must match your MATLAB release series.

## Attribution

The `tools/SRD/` directory contains MATLAB code from *Software Receiver Design* by C. Richard Johnson, Jr. and William A. Sethares ([github.com/gopmc/SRD](https://github.com/gopmc/SRD)), used for educational purposes.

## License

Provided as-is for educational and research purposes. Check MATLAB toolbox license constraints before reuse.
