# Dataflow Diagram — gui_alternate

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                         SignalDashboard  (main_window.py)                            │
│                                                                                     │
│    ┌─────────────┐  ┌─────────────┐  ┌────────────┐  ┌───────────┐  ┌───────────┐  │
│    │  Waveform    │  │  Channel &  │  │    ML      │  │ Inference │  │  Evaluate  │  │
│    │  Selection   │  │    Noise    │  │  Training  │  │  Results  │  │   Model    │  │
│    └──────┬───────┘  └──────┬──────┘  └─────┬──────┘  └─────┬─────┘  └─────┬─────┘  │
│           │                 │               │               │               │        │
│           │   Signal(       │               │  Signal(      │               │        │
│           │   object,       │               │  str, list)   │               │        │
│           │   float, str)   │               │               │               │        │
│           ├────────────────►│               ├──────────────►│               │        │
│           │  waveform_      │               │  trained_     ├ ─ ─ ─ ─ ─ ─ ─│        │
│           │  generated      │               │  model_ready  │               │        │
│           │                 │               ├──────────────────────────────►│        │
│           │                 │               │               │               │        │
└───────────┼─────────────────┼───────────────┼───────────────┼───────────────┼────────┘
            │                 │               │               │               │
            ▼                 ▼               ▼               ▼               ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐
│ MATLAB Engine │  │    Sionna    │  │   PyTorch    │  │  PyTorch │  │ MATLAB + Torch│
│  (Waveform)   │  │  Ray Tracer  │  │   Trainer    │  │ Inference│  │  (Generate &  │
│               │  │              │  │              │  │          │  │   Classify)   │
└───────────────┘  └──────────────┘  └──────────────┘  └──────────┘  └──────────────┘
```

---

## Detailed Tab-Level Flows

### 1. Waveform Selection Tab

```
 User Input                        Backend                            Output
┌──────────┐                  ┌─────────────────┐
│Modulation│─┐                │                 │
│  (combo) │ │                │  gui_elements   │
├──────────┤ │  build         │  .Waveform(     │
│  fs, fc  │ ├──params──────► │    eng, fs,     │
│  M, var  │ │                │    modulation,  │
│  Nsymb   │ │                │    ...)         │
├──────────┤ │                │                 │
│Pulse Shp │─┘                └────────┬────────┘
│alpha,span│                           │
└──────────┘                  generate_data()
                                       │
     ┌────────────────┐                │
     │ MATLAB Engine  │◄───────────────┘
     │                │    calls modulation-
     │  PAM_mod()     │    specific .m fn
     │  QAM_mod()     │
     │  PSK_mod()     │          ┌──────────────────────────────────────────┐
     │  OFDM_mod()    │          │                                          │
     │  plotspec_gui()│──────────┤  Returns: signal (np.array), fs (float)  │
     └────────────────┘          │                                          │
                                 └──────────────┬───────────────────────────┘
                                                │
                        ┌───────────────────────┼──────────────────────┐
                        │                       │                      │
                        ▼                       ▼                      ▼
               ┌────────────────┐    ┌──────────────────┐    ┌────────────────┐
               │ Time Domain    │    │ Freq Domain Plot │    │  IQ Scatter    │
               │ Plot (widget)  │    │  + Spectrogram   │    │  Plot (widget) │
               └────────────────┘    └──────────────────┘    └────────────────┘
                        │
                        ▼
          ┌──────────────────────────┐         ┌──────────────────────────────┐
          │  emit waveform_generated │────────►│  ChannelNoiseTab             │
          │  (signal, fs, modulation)│         │  .receive_waveform()         │
          └──────────────────────────┘         └──────────────────────────────┘
                        │
                        ▼
          ┌──────────────────────────┐
          │ "Save to Dataset"        │───► waveform_data/<mod>/data_N.npy
          │ "Batch Generate"         │───► DatasetGeneratorThread
          └──────────────────────────┘         │
                                               ├── sample_progress(cur, total)
                                               └── generation_finished(dir)
```

### 2. Channel & Noise Tab (Sionna)

```
 User Input                   Backend (main thread)                    Output
┌──────────────┐
│ Scene (combo)│─┐
├──────────────┤ │
│ Frequency    │ │       ┌───────────────────────────────────────┐
│ Max Depth    │ │       │                                       │
├──────────────┤ ├──────►│  run_sionna_raytrace(config, prog)    │
│ TX x, y, z   │ │       │                                       │
├──────────────┤ │       │  1. load_scene(xml_path)              │
│ RX x, y, z   │ │       │  2. PlanarArray (TX + RX)             │
├──────────────┤ │       │  3. scene.add(Transmitter, Receiver)  │
│ Antenna Cfg  │─┘       │  4. PathSolver()(scene, max_depth)    │
└──────────────┘         │  5. paths.cir() → (a, tau)            │
                         │  6. np.array() → SionnaResult          │
  on_progress() ◄────────│  [processEvents() keeps UI alive]     │
                         └───────────────────┬───────────────────┘
                                             │
            ┌────────────────────────────────┬┴──────────────────────────────┐
            │                                │                               │
            ▼                                ▼                               ▼
   ┌─────────────────┐            ┌──────────────────┐            ┌──────────────────┐
   │  CIR Stem Plot  │            │  3D Scene View   │            │   Path Info      │
   │  (Matplotlib)   │            │  (sionna-vispy   │            │   (text label)   │
   │                 │            │   Previewer)     │            │                  │
   │  tau vs |a|     │            │                  │            │  num_paths       │
   └─────────────────┘            │  plot_scene()    │            │  delay_spread    │
                                  │  plot_radio_     │            │  dominant path   │
                                  │    devices()     │            └──────────────────┘
                                  │  plot_paths()    │
                                  │                  │
                                  │  Camera state    │
                                  │  preserved on    │
                                  │  re-run          │
                                  └──────────────────┘

                         ┌──────────────────────────────────┐
  _waveform_signal ─────►│  "Apply CIR to Last Waveform"    │
  (from Waveform tab)    │                                  │
                         │  SionnaResult.apply_to_signal()  │
                         │  1. tau → sample delays          │
                         │  2. build FIR filter h[]         │
                         │  3. np.convolve(signal, h)       │
                         └──────────────┬───────────────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │ Before / After   │
                               │ Comparison Plot  │
                               │ (original vs     │
                               │  convolved)      │
                               └─────────────────┘

  ┌──────────────────────────────────────────────────────────────────────┐
  │  CIR Cache (LRU, max 10)                                           │
  │                                                                      │
  │  Key: (scene, tx_pos, rx_pos, freq, depth, antenna_cfg...)          │
  │  Val: SionnaResult (a, tau, _scene, _paths)                         │
  │                                                                      │
  │  cache_get(config) → hit? skip ray tracing                          │
  │  cache_put(config, result) → store for reuse                        │
  └──────────────────────────────────────────────────────────────────────┘
```

### 3. ML Training Tab

```
 User Input                    Backend (QThread)                      Output
┌────────────────┐
│ "Add Data      │─────► QFileDialog ──► file_label_pairs[]
│  Folder"       │                       [(path, label_idx), ...]
│                │
│ "Quick Load    │─────► scan waveform_data/<class>/*.npy
│  Dataset"      │       auto-build file_label_pairs[]
├────────────────┤
│ Model (combo)  │──┐
│  SimpleCNN     │  │
│  TinyConv      │  │
│  MLP           │  │
│  ResNet1D      │  │    ┌──────────────────────────────────────────────┐
│  Optimized     │  │    │                                              │
├────────────────┤  │    │  TrainerThread(QThread)                      │
│ Epochs         │  │    │                                              │
│ Batch Size     │  ├───►│  1. Load .npy files from file_label_pairs   │
│ Learning Rate  │  │    │  2. Preprocess:                              │
│ Val Split      │  │    │     - IQ models: split into 2-ch (I, Q)     │
│ Weight Decay   │  │    │     - Others: flatten to 1-ch                │
│ Label Smooth   │  │    │     - Normalize per-sample                   │
│ Grad Clip      │  │    │     - Pad/truncate to target length          │
├────────────────┤  │    │  3. Train/val split                          │
│ Model Hparams  │  │    │  4. DataLoader(batch_size, shuffle)          │
│ (if ResNet1D): │  │    │  5. Optimizer: AdamW + OneCycleLR            │
│  base_filters  │──┘    │  6. Loss: CrossEntropy (label smoothing)     │
│  dropout       │       │  7. Train loop (mixed precision if CUDA)     │
└────────────────┘       │  8. Best-val-loss checkpoint                 │
                         │                                              │
  progress signal ◄──────│  emit progress(epoch, total, t_loss,         │
  (per epoch)            │               v_loss, t_acc, v_acc)          │
                         │                                              │
                         └──────────────────────┬───────────────────────┘
                                                │
                                                │ on finished:
                                                ▼
                              ┌──────────────────────────────────────────┐
                              │  Save to models/ directory               │
                              │                                          │
                              │  <model>_<timestamp>.pth  (state dict)   │
                              │  <model>_<timestamp>.json (metadata)     │
                              │    {                                      │
                              │      "model_name": "ResNet1DOptimized",  │
                              │      "class_labels": ["PAM","QAM",...],  │
                              │      "num_classes": N,                   │
                              │      "input_channels": 1 or 2,           │
                              │      "signal_length": 2048               │
                              │    }                                      │
                              └──────────────────┬───────────────────────┘
                                                 │
                                    emit trained_model_ready
                                      (model_path, labels)
                                                 │
                              ┌──────────────────┼──────────────────┐
                              │                                     │
                              ▼                                     ▼
                   ┌────────────────────┐              ┌────────────────────┐
                   │ InferenceResultsTab│              │  EvaluateModelTab  │
                   │ .receive_trained_  │              │  .receive_trained_ │
                   │  model()           │              │   model()          │
                   └────────────────────┘              └────────────────────┘

  Training UI displays:
  ┌──────────────────────────────────────────────┐
  │  Loss Curve        │  Accuracy Curve         │
  │  (train + val)     │  (train + val)          │
  │  per epoch         │  per epoch              │
  ├──────────────────────────────────────────────┤
  │  Stats: best val loss, final accuracy,       │
  │         total epochs, model param count       │
  └──────────────────────────────────────────────┘
```

### 4. Inference Results Tab

```
 User Input                    Processing                              Output
┌────────────────┐
│ "Load Model"   │─────► QFileDialog → .pth file
│                │       Also loads companion .json metadata
│                │       → torch.load(state_dict)
│                │       → get_model(name, classes, length, **hparams)
│                │       → model.load_state_dict()
│                │       → model.eval()
│                │
│  OR auto-load  │◄───── trained_model_ready signal from ML Training
├────────────────┤
│ "Load Test     │─────► QFileDialog or quick-load
│  Data Folder"  │       scan waveform_data/<class>/*.npy
│                │       → eval_data[(signal, label), ...]
│                │       → eval_labels["PAM", "QAM", ...]
└────────┬───────┘
         │
         │  ┌─────────────────────────────────────────────────────────┐
         │  │   Data Preprocessing                                    │
         │  │                                                         │
         │  │  for each .npy file:                                    │
         │  │   1. Load signal = np.load(path)                        │
         │  │   2. If IQ model: reshape to 2-channel (I, Q)           │
         │  │   3. Normalize: (x - mean) / (std + eps)                │
         │  │   4. Pad or truncate to TARGET_LENGTH (2048)             │
         │  │   5. Stack into batch tensor                             │
         │  └─────────────────────────────────────────────────────────┘
         │
         ├─────────────────────┬─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Confusion       │  │ Classification  │  │  ROC Curve       │
│ Matrix          │  │ Report          │  │                  │
│                 │  │                 │  │                  │
│ _batched_       │  │ _batched_       │  │ _batched_        │
│  inference()    │  │  inference()    │  │  inference()     │
│       │         │  │       │         │  │       │          │
│       ▼         │  │       ▼         │  │       ▼          │
│ sklearn.metrics │  │ classification_ │  │ roc_curve()      │
│ .confusion_     │  │  report()       │  │ auc()            │
│  matrix()       │  │                 │  │                  │
│       │         │  │       │         │  │       │          │
│       ▼         │  │       ▼         │  │       ▼          │
│ Heatmap Plot    │  │ Text Display    │  │ Multi-class      │
│ (Matplotlib)    │  │ (QLabel)        │  │ ROC Plot         │
└─────────────────┘  └─────────────────┘  └──────────────────┘
```

### 5. Evaluate Model Tab

```
 User Input                     Processing                            Output
┌────────────────┐
│ "Load Model"   │──► same as Inference Tab (QFileDialog or auto-load)
├────────────────┤
│ Modulation     │─┐
│ fs, fc, M, var │ │
│ Nsymb          │ │  ┌──────────────────────────────────────────┐
│ Pulse Shape    │ ├─►│  Waveform(eng, fs, mod, ...).generate()  │──► MATLAB engine
│ alpha, span    │ │  └──────────────────┬───────────────────────┘
└────────────────┘ │                     │
                   │                     ▼ raw signal (np.array)
                   │  ┌──────────────────────────────────────────┐
                   │  │  _classify_signal(data)                  │
  "▶ Generate     │  │                                          │
     & Classify"──┘  │  1. Preprocess (IQ split, normalize,    │
                     │     pad to target length)                 │
                     │  2. model(tensor) → logits                │
                     │  3. softmax → class probabilities         │
                     │  4. argmax → predicted label              │
                     └──────────────────┬───────────────────────┘
                                        │
                     ┌──────────────────┼──────────────────────┐
                     │                  │                      │
                     ▼                  ▼                      ▼
            ┌─────────────┐   ┌─────────────────┐   ┌────────────────────┐
            │ Result Label│   │ Waveform Plots  │   │ Probability Bar    │
            │ "Predicted: │   │ (Time, Freq,    │   │ Chart              │
            │  QAM-16"    │   │  IQ, Spectro)   │   │ (per-class conf.)  │
            │ confidence% │   │                 │   │                    │
            └─────────────┘   └─────────────────┘   └────────────────────┘
```

---

## Cross-Tab Signal Wiring (main_window.py)

```
┌─────────────────────┐     waveform_generated      ┌─────────────────────┐
│                     │     Signal(object,float,str)  │                     │
│  WaveformSelection  │─────────────────────────────►│  ChannelNoiseTab    │
│  Tab                │                               │  .receive_waveform()│
│                     │    (signal_np, fs, mod_str)   │                     │
└─────────────────────┘                               └─────────────────────┘


┌─────────────────────┐     trained_model_ready      ┌─────────────────────┐
│                     │     Signal(str, list)          │                     │
│  MLTrainingTab      │─────────────────────────────►│  InferenceResultsTab│
│                     │                               │  .receive_trained_  │
│                     │    (model_path, labels)       │   model()           │
│                     │          │                     └─────────────────────┘
│                     │          │
│                     │          │                     ┌─────────────────────┐
│                     │          └────────────────────►│  EvaluateModelTab   │
│                     │                               │  .receive_trained_  │
│                     │                               │   model()           │
└─────────────────────┘                               └─────────────────────┘
```

---

## External Systems & File I/O

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MATLAB Engine                                   │
│                                                                         │
│  Started once in main_window.py                                         │
│  Shared by: WaveformSelectionTab, EvaluateModelTab                      │
│                                                                         │
│  Functions called:                                                       │
│    PAM_mod(fs, Tsymb, Nsymb, fc, M, var, alpha, span, pulse_shape)      │
│    QAM_mod(fs, Tsymb, Nsymb, fc, M, var, alpha, span, pulse_shape)      │
│    PSK_mod(fs, Tsymb, Nsymb, fc, M, var, alpha, span, pulse_shape)      │
│    OFDM_mod(fs, Tsymb, Nsymb, fc, M, var)                               │
│    plotspec_gui(data, 1/fs) → (freqs, spectrum)                          │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                           File System                                    │
│                                                                         │
│  waveform_data/                                                          │
│  ├── PAM/                                                                │
│  │   ├── data_0.npy          ◄── WaveformTab "Save" / Batch Generate    │
│  │   ├── data_1.npy              MLTrainingTab "Quick Load" reads these  │
│  │   └── ...                     InferenceTab "Quick Load" reads these   │
│  ├── QAM/                                                                │
│  │   └── ...                                                             │
│  ├── PSK/                                                                │
│  │   └── ...                                                             │
│  └── OFDM/                                                               │
│      └── ...                                                             │
│                                                                         │
│  models/                                                                 │
│  ├── ResNet1D_20250218_143022.pth    ◄── TrainerThread saves             │
│  ├── ResNet1D_20250218_143022.json       InferenceTab / EvaluateTab load │
│  └── ...                                                                 │
│                                                                         │
│  sionna/austin/                                                          │
│  ├── UT_Twin_1.xml           ◄── Sionna load_scene() reads              │
│  ├── Austin_2.xml                                                        │
│  ├── Austin_Downtown.xml                                                 │
│  └── Austin_suburban.xml                                                 │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      Sionna RT + DrJIT + Mitsuba                         │
│                                                                         │
│  CONSTRAINT: All operations must run on the MAIN THREAD                  │
│  (DrJIT scope-ordering error if used cross-thread)                       │
│                                                                         │
│  load_scene() → Scene object (Mitsuba XML)                               │
│  PlanarArray() → antenna config                                          │
│  Transmitter() / Receiver() → radio devices                              │
│  PathSolver()() → ray-traced paths                                       │
│  paths.cir() → (a, tau) tensors                                         │
│                                                                         │
│  Results cached in LRU (max 10 entries, keyed by full config tuple)      │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      PyTorch (Training + Inference)                       │
│                                                                         │
│  Training: runs in QThread (TrainerThread)                               │
│    - AdamW optimizer + OneCycleLR scheduler                              │
│    - CrossEntropyLoss with optional label smoothing                      │
│    - Mixed precision (torch.amp) if CUDA available                       │
│    - Best-val-loss checkpointing                                         │
│                                                                         │
│  Inference: runs on main thread                                          │
│    - Batched (batch_size=64) to avoid OOM                                │
│    - model.eval() + torch.no_grad()                                      │
│    - softmax → probabilities → argmax → prediction                       │
│                                                                         │
│  Models:                                                                 │
│    SimpleCNN      — Conv1d(1→16→32) + FC         input: (B, 1, L)        │
│    TinyConv       — Conv1d(1→8) + FC             input: (B, 1, L)        │
│    MLP            — FC(L→512→256→C)              input: (B, L)           │
│    ResNet1D       — ResBlocks + SE + FC          input: (B, 2, L)  [IQ]  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Complete End-to-End Pipeline

```
                    ┌──────────┐
                    │   User   │
                    └────┬─────┘
                         │ configures waveform params
                         ▼
                ┌─────────────────┐
                │  Waveform Tab   │
                │  "▶ Generate"   │
                └────────┬────────┘
                         │ MATLAB engine call
                         ▼
                ┌─────────────────┐
                │  MATLAB .m fn   │───► signal (np.array), fs
                └────────┬────────┘
                         │
            ┌────────────┼───────────────────────┐
            │            │                       │
            ▼            ▼                       ▼
   ┌──────────────┐  ┌────────────┐     ┌──────────────────┐
   │ Visualization│  │"Save" /    │     │ Channel Tab      │
   │ (Time, Freq, │  │"Batch Gen" │     │ receive_waveform │
   │  IQ, Spectro)│  │            │     └────────┬─────────┘
   └──────────────┘  └─────┬──────┘              │ user clicks
                           │                     │ "Run Ray Tracing"
                           ▼                     ▼
                   ┌──────────────┐     ┌──────────────────┐
                   │ waveform_data│     │  Sionna RT       │
                   │ /<class>/    │     │  load_scene →    │
                   │  data_N.npy  │     │  PathSolver →    │
                   └───────┬──────┘     │  CIR (a, tau)    │
                           │            └────────┬─────────┘
                           │                     │
                           │            ┌────────┴─────────┐
                           │            │                  │
                           │            ▼                  ▼
                           │   ┌──────────────┐   ┌──────────────┐
                           │   │ 3D Preview   │   │ "Apply CIR"  │
                           │   │ (VisPy)      │   │ convolve     │
                           │   └──────────────┘   │ signal ⊛ h   │
                           │                      └──────┬───────┘
                           │                             │
                           │                             ▼
                           │                    ┌──────────────┐
                           │                    │ Before/After │
                           │                    │ Plot         │
                           │                    └──────────────┘
                           │
                           │  user loads dataset
                           ▼
                   ┌──────────────────┐
                   │  ML Training Tab │
                   │  TrainerThread   │
                   │                  │
                   │  load .npy files │
                   │  preprocess IQ   │
                   │  train model     │
                   │  save .pth+.json │
                   └────────┬─────────┘
                            │
                   emit trained_model_ready
                     (model_path, labels)
                            │
               ┌────────────┴────────────┐
               │                         │
               ▼                         ▼
      ┌─────────────────┐      ┌─────────────────┐
      │  Inference Tab  │      │  Evaluate Tab   │
      │                 │      │                 │
      │  load test data │      │  generate new   │
      │  run batched    │      │  waveform via   │
      │  inference      │      │  MATLAB, then   │
      │                 │      │  classify with  │
      │  ┌───────────┐  │      │  loaded model   │
      │  │Confusion  │  │      │                 │
      │  │Matrix     │  │      │  ┌───────────┐  │
      │  ├───────────┤  │      │  │Prediction │  │
      │  │Report     │  │      │  │Label +    │  │
      │  ├───────────┤  │      │  │Confidence │  │
      │  │ROC Curve  │  │      │  ├───────────┤  │
      │  └───────────┘  │      │  │Prob. Bar  │  │
      └─────────────────┘      │  │Chart      │  │
                               │  └───────────┘  │
                               └─────────────────┘
```
