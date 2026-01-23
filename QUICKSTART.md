# RFML Quick Start Guide

## What You Have Now

You have successfully integrated the **ML training pipeline** from your **Spectrum-Scrapers** project into the main RFML application!

The app now has **two main tabs**:
1. 🔊 **Generate Waveforms** - Create RF signals with various modulations
2. 🧠 **Classify Waveforms** - Train ML models to classify modulations

---

## Installation

### Prerequisites

```bash
# Python packages
pip install torch torchvision
pip install PySide6
pip install matplotlib
pip install scipy
pip install numpy
pip install matlabengine
```

### MATLAB Toolboxes Required:
- Communications Toolbox
- Wavelet Toolbox
- Signal Processing Toolbox

---

## Running the App

```bash
cd gui
python app.py
```

The application window will open with two tabs.

---

## Tab 1: Generate Waveforms

### Quick Test:
1. Select modulation: **QAM**
2. Set M: **16**
3. Click **Run**
4. View the generated waveform in all 4 plot types

### What You Can Do:
- Generate signals with different modulations: PAM, QAM, PSK, FSK, FHSS
- Configure sample rate, carrier frequency, symbol rate
- Choose pulse shaping: RRC (root raised cosine) or rectangular
- Visualize in:
  - Time domain
  - Frequency domain
  - IQ constellation
  - Spectrogram

---

## Tab 2: Classify Waveforms (NEW!)

### Quick Test (Small Dataset):

**Step 1: Generate Dataset**
1. Set "Samples per class": **100**
2. Set SNR range: **-5** to **20** dB
3. Click **"Generate Dataset"**
4. Wait ~5-10 minutes (status log shows progress)

**Step 2: Train Model**
1. Set Batch size: **16**
2. Set Max Epochs: **20**
3. Learning rate: **0.0001**
4. Click **"Start Training"**
5. Watch the training curves update in real-time!

### What Happens:
- Generates 100 samples × 7 modulations = 700 total samples
- Each sample is a CWT (Continuous Wavelet Transform) scalogram
- Random SNR between -5 and 20 dB for robustness
- Trains ResNet18 with transfer learning
- Shows live loss and accuracy curves

### Expected Results (100 samples/class):
- Training time: ~10-20 minutes (depending on GPU)
- Validation accuracy: ~70-85% (small dataset)
- Best classes: BPSK, OFDM, 4FSK
- Challenging: 8PSK vs QPSK, 16QAM vs 64QAM

### For Better Performance:

**Medium Dataset** (Recommended):
- Samples per class: **500**
- Expected accuracy: ~85-92%
- Generation time: ~20-30 minutes
- Training time: ~30-45 minutes

**Large Dataset** (Research Quality):
- Samples per class: **1000-2000**
- Expected accuracy: ~92-96%
- Generation time: ~1-2 hours
- Training time: ~1-2 hours

---

## Understanding the Plots

### Training Loss (Top Plot):
- **Blue line**: Training loss
- **Red line**: Validation loss
- **Goal**: Both should decrease and converge
- **Warning**: If train keeps dropping but val increases → overfitting

### Accuracy (Bottom Plot):
- **Blue line**: Training accuracy
- **Red line**: Validation accuracy
- **Goal**: Both should increase (ideally >85%)
- **Good sign**: Val accuracy follows train closely
- **Bad sign**: Large gap between train and val

---

## Understanding the Status Log

### Dataset Generation Messages:
```
Starting MATLAB engine...
Generating BPSK samples...
Generated 70/1400 samples...
Generating QPSK samples...
...
Dataset generated: 1400 samples
Images shape: (1400, 224, 224)
```

### Training Messages:
```
Training set: 1120 samples
Validation set: 280 samples
Created ResNet18 model
Epoch 1: Train Loss=1.8234, Train Acc=0.3214, Val Loss=1.5432, Val Acc=0.4286
Epoch 2: Train Loss=1.2156, Train Acc=0.5625, Val Loss=1.1234, Val Acc=0.6071
...
✓ Model saved (Val Loss: 0.4521, Val Acc: 0.8571)
Early stopping triggered at epoch 18
Training complete!
```

---

## Modulation Types Supported

### 7-Class Classification:

| Class | Description | Key Features |
|-------|-------------|--------------|
| **BPSK** | Binary Phase Shift Keying | 2 constellation points, simplest |
| **QPSK** | Quadrature PSK | 4 constellation points |
| **8PSK** | 8-ary PSK | 8 points on unit circle |
| **16QAM** | 16-Quadrature Amplitude Mod | 4×4 grid constellation |
| **64QAM** | 64-QAM | 8×8 grid constellation |
| **4FSK** | 4-ary Frequency Shift Keying | 4 frequency tones |
| **OFDM** | Orthogonal Frequency Division Multiplex | Multi-carrier, unique spectrum |

---

## Tips for Best Results

### Dataset Generation:
✅ Start with 100-200 samples for quick testing
✅ Use 500-1000 samples for production models
✅ Wider SNR range (-10 to 25 dB) improves robustness
✅ Let MATLAB engine warm up on first run

### Training:
✅ Batch size 16-32 works well for most cases
✅ Let early stopping do its job (patience=7)
✅ Lower learning rate (0.0001 or 0.00001) is safer
✅ Watch for convergence (both curves stabilizing)

### Common Issues:
❌ **"Out of memory"** → Reduce batch size to 8 or 4
❌ **Training loss NaN** → Lower learning rate
❌ **Val accuracy stuck** → Need more data or augmentation
❌ **Overfitting** → Increase dropout or weight decay

---

## What the Model Learns

The classifier learns to recognize modulation types based on their **time-frequency signatures** (CWT scalograms):

- **BPSK**: Simple two-state pattern
- **QPSK/8PSK**: Similar but different density
- **QAM**: Grid-like structures in phase space
- **FSK**: Distinct frequency bands over time
- **OFDM**: Multi-carrier comb structure

Each modulation has a unique "fingerprint" in the CWT domain!

---

## Saving and Loading Models

### Model Files:
- Default save location: `modulation_classifier.pth`
- Contains only model weights (not full model)
- Can be loaded later for inference

### To Use a Saved Model (Future Feature):
```python
# Will be added in future updates
model = create_model(num_classes=7)
model.load_state_dict(torch.load('modulation_classifier.pth'))
model.eval()
```

---

## Performance Benchmarks

### From Original Spectrum-Scrapers Results:

**7-Class Model (1000 samples/class)**:
```
              precision    recall  f1-score   support
BPSK              0.96      0.98      0.97       142
QPSK              0.89      0.87      0.88       138
8PSK              0.84      0.81      0.83       145
16QAM             0.88      0.91      0.89       137
64QAM             0.87      0.89      0.88       143
4FSK              0.93      0.95      0.94       141
OFDM              0.97      0.96      0.96       154

accuracy                              0.91       1000
macro avg         0.91      0.91      0.91       1000
```

**Key Insights**:
- Overall accuracy: **~91%**
- Best performers: BPSK (97%), OFDM (96%), 4FSK (94%)
- Most confused: 8PSK ↔ QPSK (similar phase patterns)

---

## Next Steps

### Immediate:
1. ✅ Generate a small test dataset (100 samples)
2. ✅ Train for 10-20 epochs to verify it works
3. ✅ Check training curves converge properly

### Short-term:
1. Generate larger dataset (500+ samples)
2. Train to completion (let early stopping work)
3. Analyze which classes are hardest to classify
4. Experiment with different SNR ranges

### Future Enhancements:
1. **Real-time Inference**: Classify signals from Tab 1
2. **Confusion Matrix**: Visualize misclassifications
3. **SNR Analysis**: Plot accuracy vs SNR curve
4. **3-Class Mode**: FSK vs OFDM vs Neither
5. **Export/Import**: Save datasets and models
6. **Model Comparison**: Try different architectures

---

## Troubleshooting

### App Won't Start:
```bash
# Check dependencies
pip list | grep -E "torch|PySide6|scipy|numpy"

# Verify MATLAB engine
python -c "import matlab.engine; print('MATLAB OK')"
```

### MATLAB Engine Issues:
- Make sure MATLAB is installed and activated
- Check `matlabengine` package is installed
- Required toolboxes must be licensed

### Training Crashes:
- **GPU memory error**: Reduce batch size
- **CPU only**: Set `device='cpu'` (slower but works)
- **NaN loss**: Lower learning rate to 0.00001

### Dataset Generation Slow:
- Normal! CWT computation is computationally expensive
- 1400 samples (200 per class) takes ~15-25 minutes
- Use the time to grab coffee ☕

---

## Understanding Your Worktree

You're currently in: `C:\Users\madan\.claude-worktrees\FH11_RFML\bold-wilson`

This is a **git worktree**, not a copy:
- Linked to main repo: `C:\Users\madan\FH11_RFML`
- You can commit changes here
- Merge back to main when ready
- Useful for working on features in parallel

---

## Summary

✨ **You now have a complete ML pipeline integrated into your RFML app!**

**What works:**
- ✅ Generate 7 types of modulated signals
- ✅ Visualize signals in 4 different domains
- ✅ Generate CWT-based training datasets
- ✅ Train ResNet18 classifier with transfer learning
- ✅ Live training progress monitoring
- ✅ Automatic model saving with early stopping

**What's next:**
- 🔄 Real-time inference on generated waveforms
- 📊 Confusion matrix visualization
- 💾 Dataset save/load functionality
- 📈 Performance analysis tools

Happy training! 🚀
