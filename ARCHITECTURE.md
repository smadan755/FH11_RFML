# RFML Application Architecture

## Updated Application Structure (After ML Integration)

```
┌─────────────────────────────────────────────────────────────────┐
│                         gui/app.py                              │
│                      Main Application                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              QTabWidget (Main Menu)                      │  │
│  │                                                          │  │
│  │  ┌────────────────────┐  ┌──────────────────────────┐  │  │
│  │  │  Tab 1: Generate   │  │  Tab 2: Classify         │  │  │
│  │  │     Waveforms      │  │     Waveforms (NEW!)     │  │  │
│  │  │                    │  │                          │  │  │
│  │  │  MainWindow()      │  │     MLWidget()           │  │  │
│  │  └────────────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tab 1: Waveform Generation (main_window.py)

```
┌──────────────────────────────────────────────────────────────────┐
│                        MainWindow                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌──────────────────────────────────┐   │
│  │ SelectionWidget │     │        QTabWidget                │   │
│  │                 │     │                                  │   │
│  │ • Modulation    │     │  ┌──────────────────────────┐   │   │
│  │ • fs, Tsymb     │────▶│  │ Time Domain Plot         │   │   │
│  │ • fc, M, Var    │     │  └──────────────────────────┘   │   │
│  │ • Nsymb         │     │  ┌──────────────────────────┐   │   │
│  │ • Pulse Shape   │     │  │ Frequency Domain Plot    │   │   │
│  │ • Alpha, Span   │     │  └──────────────────────────┘   │   │
│  │                 │     │  ┌──────────────────────────┐   │   │
│  │ [Run Button]    │     │  │ IQ Constellation Plot    │   │   │
│  │                 │     │  └──────────────────────────┘   │   │
│  └─────────────────┘     │  ┌──────────────────────────┐   │   │
│                          │  │ Spectrogram Plot         │   │   │
│                          │  └──────────────────────────┘   │   │
│                          └──────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │    gui_elements.py          │
                    │                             │
                    │  • WaveformConfig           │
                    │  • MATLABGenerator          │
                    │  • Waveform                 │
                    └─────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │  waveform_generator.m       │
                    │                             │
                    │  • generate_symbols()       │
                    │  • upfirdn() pulse shaping  │
                    │  • upconvert_to_passband()  │
                    └─────────────────────────────┘
```

---

## Tab 2: ML Classification (ml.py - NEW!)

```
┌────────────────────────────────────────────────────────────────────┐
│                           MLWidget                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────┐     ┌───────────────────────────────┐   │
│  │  Left Panel:         │     │  Right Panel:                 │   │
│  │  Configuration       │     │  Training Visualization       │   │
│  │                      │     │                               │   │
│  │ ┌──────────────────┐ │     │  ┌─────────────────────────┐ │   │
│  │ │ Dataset Gen      │ │     │  │                         │ │   │
│  │ │ • Samples/class  │ │     │  │  Training Loss Curve    │ │   │
│  │ │ • SNR range      │ │     │  │  ┌─────────────────┐   │ │   │
│  │ │ [Generate]───────┼─┼─────┼──│  │  Train vs Val   │   │ │   │
│  │ └──────────────────┘ │     │  │  └─────────────────┘   │ │   │
│  │                      │     │  │                         │ │   │
│  │ ┌──────────────────┐ │     │  │  Accuracy Curve         │ │   │
│  │ │ Training Config  │ │     │  │  ┌─────────────────┐   │ │   │
│  │ │ • Batch size     │ │     │  │  │  Train vs Val   │   │ │   │
│  │ │ • Epochs         │ │     │  │  └─────────────────┘   │ │   │
│  │ │ • Learning rate  │ │     │  │                         │ │   │
│  │ │ [Start Training]─┼─┼─────┼──│  Live Updates!          │ │   │
│  │ └──────────────────┘ │     │  │                         │ │   │
│  │                      │     │  └─────────────────────────┘ │   │
│  │ ┌──────────────────┐ │     │                               │   │
│  │ │ Status Log       │ │     └───────────────────────────────┘   │
│  │ │ [Real-time text] │ │                                         │
│  │ └──────────────────┘ │                                         │
│  │                      │                                         │
│  │ [Export Model]       │                                         │
│  └──────────────────────┘                                         │
└────────────────────────────────────────────────────────────────────┘
```

---

## ML Training Pipeline Flow

```
User Clicks "Generate Dataset"
            │
            ▼
┌─────────────────────────────┐
│  DatasetGeneratorThread     │  ◄─── QThread (background)
│                             │
│  For each modulation type:  │
│    For each sample:         │
│      1. Generate signal     │────► MATLAB engine
│         (MATLAB workspace)  │      • pskmod()
│      2. Add AWGN noise      │      • qammod()
│      3. Compute CWT         │      • fskmod()
│      4. Resize to 224x224   │      • cwt()
│      5. Normalize [0,1]     │
│                             │
│  Emit: (images, labels)     │
└─────────────────────────────┘
            │
            ▼
      Dataset Ready!
      (stored in memory)
            │
            ▼
User Clicks "Start Training"
            │
            ▼
┌─────────────────────────────┐
│  Create Train/Val Split     │
│  (80% / 20%)                │
└─────────────────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  Create DataLoaders         │
│  • Train: with augmentation │
│  • Val: no augmentation     │
└─────────────────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  Create ResNet18 Model      │
│  • Load ImageNet weights    │
│  • Replace FC layer         │
│  • Add dropout layers       │
└─────────────────────────────┘
            │
            ▼
┌─────────────────────────────┐
│   TrainingThread            │  ◄─── QThread (background)
│                             │
│   For each epoch:           │
│     1. Training phase       │────► Forward pass
│     2. Validation phase     │      Backward pass
│     3. Emit metrics         │      Optimizer step
│     4. Update plots         │
│     5. Early stopping check │
│     6. Save best model      │
│                             │
│   Emit: trained_model       │
└─────────────────────────────┘
            │
            ▼
   Training Complete!
   Model saved to .pth
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATLAB Signal Generation                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Random modulation type
                    Random SNR in range
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │  MATLAB Workspace: Generate Signal       │
        │                                          │
        │  data = randi([0 M-1], N, 1)            │
        │  tx = mod_function(data, M)  ◄───────────┼─── pskmod/qammod/fskmod
        │  rx = awgn(tx, SNR, 'measured')         │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │  MATLAB: Compute CWT                     │
        │                                          │
        │  [cfs, frq] = cwt(real(rx), fs)         │
        │  P = abs(cfs).^2                        │
        │  P = normalize(P)                       │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │  Python: Resize & Format                 │
        │                                          │
        │  zoom(P, target_size)                   │
        │  → 224×224 grayscale image              │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │  ModulationDataset                       │
        │                                          │
        │  if augment:                            │
        │    - Random flip                        │
        │    - Time shift                         │
        │    - Add noise                          │
        │                                          │
        │  Convert to RGB (3 channels)            │
        │  → torch.Tensor                         │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │  ResNet18 Feature Extraction             │
        │                                          │
        │  Conv layers (pretrained on ImageNet)   │
        │  → 512-dim feature vector               │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │  Custom Classifier Head                  │
        │                                          │
        │  Dropout(0.5)                           │
        │  → Linear(512 → 128)                    │
        │  → BatchNorm + ReLU + Dropout           │
        │  → Linear(128 → 7 classes)              │
        └──────────────────────────────────────────┘
                              │
                              ▼
                  [BPSK, QPSK, 8PSK, 16QAM, 64QAM, 4FSK, OFDM]
```

---

## Class Hierarchy

```
QMainWindow
    └── App (app.py)
        ├── MainWindow (main_window.py)
        │   ├── SelectionWidget
        │   ├── PlottingWidget
        │   ├── FreqDomainPlot
        │   ├── IQDomainPlot
        │   └── SpectrogramPlot
        │
        └── MLWidget (ml.py) ◄─── NEW!
            ├── DatasetGeneratorThread (QThread)
            ├── TrainingThread (QThread)
            └── ModulationDataset (torch Dataset)
```

---

## Dependencies Graph

```
app.py
 ├── main_window.py
 │    ├── gui_elements.py
 │    │    ├── WaveformConfig
 │    │    ├── MATLABGenerator ───► waveform_generator.m (MATLAB)
 │    │    └── Waveform
 │    └── PySide6, matplotlib, scipy
 │
 └── ml.py ◄─── NEW!
      ├── DatasetGeneratorThread
      │    └── MATLAB engine (signal generation + CWT)
      ├── TrainingThread
      │    └── PyTorch (ResNet18 training)
      └── ModulationDataset
           └── PyTorch Dataset
```

---

## Shared Resources

```
┌─────────────────────────────────────────────────────────┐
│              Shared MATLAB Engine (Potential)           │
│                                                         │
│  Currently: Separate instances per tab                 │
│  Future: Single shared engine for efficiency           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Shared Signal Generation                   │
│                                                         │
│  Possible Future Feature:                              │
│  Generate in Tab 1 → Classify in Tab 2                │
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
bold-wilson/
├── gui/
│   ├── app.py                    ◄─── Entry point (NEW!)
│   ├── main_window.py            ◄─── Tab 1: Waveform generation
│   ├── ml.py                     ◄─── Tab 2: ML training (NEW!)
│   ├── gui_elements.py           ◄─── Waveform classes
│   └── waveform_functions/
│       ├── waveform_generator.m  ◄─── Unified MATLAB generator
│       ├── plotspec_gui.m
│       └── (legacy wrappers)
│
├── augmentation/
│   ├── augmentation.py           ◄─── Noise blocks
│   └── __init__.py
│
├── ML_INTEGRATION.md             ◄─── This documentation (NEW!)
├── ARCHITECTURE.md               ◄─── Architecture diagram (NEW!)
└── README.md                     ◄─── Original project README
```

---

## Execution Flow Summary

### Starting the Application:
```bash
cd gui
python app.py
```

### Typical User Workflow:

**Option A: Generate & Visualize**
1. Go to "Generate Waveforms" tab
2. Select modulation type
3. Configure parameters
4. Click "Run"
5. View plots: Time/Freq/IQ/Spectrogram

**Option B: Train Classifier**
1. Go to "Classify Waveforms" tab
2. Configure dataset (samples, SNR)
3. Click "Generate Dataset" → wait
4. Configure training (batch, epochs, LR)
5. Click "Start Training" → watch live curves
6. Wait for completion → model saved

**Option C (Future): Generate + Classify**
1. Generate waveform in Tab 1
2. Switch to Tab 2
3. Classify the generated waveform
4. See real-time prediction

---

## Integration Points

### Where Spectrum-Scrapers Code Maps to ML Widget:

| Spectrum-Scrapers File | ML Widget Component |
|------------------------|---------------------|
| `MATLABSignalGenerator` class | `DatasetGeneratorThread._generate_matlab_signal()` |
| `generate_dataset()` function | `DatasetGeneratorThread.run()` |
| `ModulationDataset` class | `ModulationDataset` (similar, with Qt integration) |
| `create_model()` function | `MLWidget.create_model()` |
| `train_model()` function | `TrainingThread.run()` |
| `main()` execution | `MLWidget` UI workflow |

### Key Adaptations:
- **Blocking → Threading**: Long operations moved to QThread
- **Print → Signals**: Progress updates via Qt signals
- **Standalone → Widget**: Integrated into tabbed interface
- **File I/O → Memory**: Dataset kept in RAM (optional save)
- **Static plots → Live updates**: Real-time matplotlib refresh

---

This architecture provides a complete workflow from signal generation to ML classification in a unified Qt application!
