# Key Sionna & PySide6 Reference — FH11 RFML GUI

Quick-reference for the functions, classes, and patterns used throughout
the `gui_alternate/` application. Organized by subsystem.

---

## 1. Sionna RT (Ray Tracing) — `sionna.rt`

### Scene Loading

```python
from sionna.rt import load_scene

scene = load_scene("path/to/scene.xml")
```

- Loads a Mitsuba-format XML scene (buildings, materials, geometry).
- Returns a `sionna.rt.Scene` object that holds the 3D world.
- Each call creates a **fresh** scene — safe to call repeatedly.

### Antenna Arrays

```python
from sionna.rt import PlanarArray

scene.tx_array = PlanarArray(
    num_rows=1, num_cols=1,
    vertical_spacing=0.5, horizontal_spacing=0.5,
    pattern="iso",          # "iso" | "dipole" | "hw_dipole"
    polarization="V",       # "V" | "H" | "cross"
)
scene.rx_array = PlanarArray(...)   # same API
```

- Defines the antenna geometry for transmitter / receiver.
- `pattern` sets the element radiation pattern.
- `polarization` sets the element polarization.

### Transmitter & Receiver Placement

```python
from sionna.rt import Transmitter, Receiver

tx = Transmitter(name="tx", position=[x, y, z])
rx = Receiver(name="rx", position=[x, y, z], orientation=[0, 0, 0])

scene.add(tx)
scene.add(rx)
```

- Names must be unique within the scene.
- To re-place devices, remove existing ones first:

```python
for name in list(scene.transmitters.keys()):
    scene.remove(name)
for name in list(scene.receivers.keys()):
    scene.remove(name)
```

### Scene Configuration

```python
scene.frequency = 3.5e9          # carrier frequency in Hz
scene.synthetic_array = True     # use synthetic (far-field) array model
```

### Ray Tracing (Path Solving)

```python
from sionna.rt import PathSolver

solver = PathSolver()
paths = solver(scene, max_depth=5)
```

- `max_depth` controls the maximum number of reflections/diffractions.
- Higher depth = more paths found, but slower computation.

### Channel Impulse Response (CIR)

```python
a, tau = paths.cir()

a_np = np.array(a)     # complex path coefficients  [batch, rx, rx_ant, tx, tx_ant, paths, time]
tau_np = np.array(tau)  # propagation delays (seconds) [batch, rx, tx, paths]
```

- `a` contains complex amplitudes (magnitude + phase per path).
- `tau` contains the delay of each path in seconds.
- Both are multi-dimensional tensors — `.flatten()` for simple 1D plotting.

### DrJIT / Mitsuba Threading Constraint

> **All Sionna/DrJIT operations MUST run on the same thread.**

DrJIT (the JIT compiler under Mitsuba) tracks computation "scopes" per
thread. If you create scene objects on a worker thread and access them on
the main thread, DrJIT raises a scope-ordering error:

```
scope ID of predecessors must be lower
```

**Solution:** Run ray tracing synchronously on the main thread, using
`QApplication.processEvents()` to keep the GUI responsive between steps.

---

## 2. Sionna-VisPy — `sionna_vispy`

Interactive 3D scene visualization built on VisPy.

### Previewer (3D Canvas)

```python
from sionna_vispy.previewer import Previewer

canvas = Previewer(
    scene,                      # sionna.rt.Scene
    resolution=(900, 600),      # canvas pixel size
    fov=45,                     # field of view (degrees)
    background="#1e1e32",       # background color
)
```

- Extends `vispy.scene.SceneCanvas` — its `.native` property is a QWidget.
- Constructor automatically calls `plot_scene()` and `center_view()`.
- Camera: `TurntableCamera` — left-drag = orbit, scroll = zoom, right-drag = pan.

### Plotting Methods

```python
canvas.plot_radio_devices()          # TX/RX as colored spheres
canvas.plot_paths(paths)             # multipath rays as colored lines
canvas.plot_scene()                  # scene geometry (buildings, etc.)
```

### Clearing Content

```python
canvas.reset()                       # remove paths & devices, keep geometry
canvas.redraw_scene_geometry()       # remove geometry, re-plot from scene
```

- `reset()` removes objects with `persist=False` (paths, devices).
- `redraw_scene_geometry()` removes `persist=True` objects (buildings) and re-plots.
- Removal works by setting `obj.parent = None` on each VisPy visual node.

### Camera State (Preserving View Across Re-runs)

The `TurntableCamera` exposes these read/write properties:

```python
cam = canvas._camera

state = {
    "azimuth":      cam.azimuth,       # horizontal rotation (degrees)
    "elevation":    cam.elevation,     # vertical rotation (degrees)
    "distance":     cam.distance,      # zoom distance
    "center":       cam.center,        # look-at point (x, y, z)
    "scale_factor": cam.scale_factor,  # zoom scaling
}

# Restore later:
cam.azimuth      = state["azimuth"]
cam.elevation    = state["elevation"]
cam.distance     = state["distance"]
cam.center       = state["center"]
cam.scale_factor = state["scale_factor"]
```

### Embedding in Qt

```python
# Add to a QVBoxLayout:
layout.addWidget(canvas.native, 1)

# Remove later:
canvas.native.setParent(None)
layout.removeWidget(canvas.native)
canvas.close()
```

---

## 3. PySide6 — Core Widgets & Patterns

### Application & Main Window

```python
from PySide6.QtWidgets import QApplication, QMainWindow

app = QApplication(sys.argv)
app.setFont(QFont("Segoe UI", 10))

window = QMainWindow()
window.setWindowTitle("Title")
window.setMinimumSize(1400, 900)
window.setStyleSheet(qss_string)       # apply global QSS theme
window.show()
sys.exit(app.exec())
```

### Layout System

```python
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout

vbox = QVBoxLayout(parent_widget)
vbox.setContentsMargins(20, 20, 20, 20)
vbox.setSpacing(10)
vbox.addWidget(widget)
vbox.addWidget(widget, stretch=1)      # stretch factor
vbox.addLayout(child_layout)
vbox.addStretch()                      # flexible spacer
```

### Stacked Widget (Tab Content)

```python
from PySide6.QtWidgets import QStackedWidget

stack = QStackedWidget()
stack.addWidget(page_widget)
stack.setCurrentIndex(index)
```

- Each page is a full QWidget — only one visible at a time.
- Tab buttons are separate `QPushButton` widgets with `setCheckable(True)`.

### Signals & Slots

```python
from PySide6.QtCore import Signal

class MyWidget(QWidget):
    my_signal = Signal(object)         # Signal declaration (class level)

    def emit_data(self):
        self.my_signal.emit(data)      # Emit

# Connect:
widget.my_signal.connect(handler_fn)
```

- `Signal(object)` can carry any Python object.
- `Signal(str)`, `Signal(int, float)` for typed signals.
- Cross-tab wiring is done in the main window:

```python
self.tab_a.data_ready.connect(self.tab_b.receive_data)
```

### Common Input Widgets

```python
# Combo box (dropdown)
combo = QComboBox()
combo.addItems(["A", "B", "C"])
combo.currentText()                    # get selection
combo.currentTextChanged.connect(fn)   # on change

# Spin boxes
spin = QDoubleSpinBox()
spin.setRange(0.1, 100.0)
spin.setDecimals(2)
spin.setSingleStep(0.1)
spin.setSuffix(" GHz")
spin.setValue(3.5)
spin.value()                           # get current value

ispin = QSpinBox()                     # integer version
ispin.setRange(1, 16)

# Push button
btn = QPushButton("Run")
btn.setObjectName("primaryButton")     # for QSS targeting
btn.setEnabled(False)
btn.clicked.connect(fn)
btn.setCursor(Qt.PointingHandCursor)

# Checkable button (for tabs)
btn.setCheckable(True)
btn.setChecked(True)

# Group box (collapsible section)
group = QGroupBox("Title")
group.setCheckable(True)               # adds a checkbox to collapse
group.setChecked(False)                # collapsed by default
```

### Scroll Area

```python
from PySide6.QtWidgets import QScrollArea, QFrame

scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setFrameShape(QFrame.NoFrame)
scroll.setWidget(content_widget)
```

### Progress Bar

```python
from PySide6.QtWidgets import QProgressBar

bar = QProgressBar()
bar.setRange(0, 0)          # indeterminate (spinning)
bar.setRange(0, 100)        # determinate
bar.setValue(50)
bar.setVisible(False)       # hide when not in use
```

### Keeping UI Responsive During Blocking Work

```python
from PySide6.QtWidgets import QApplication

# Inside a long-running synchronous function:
status_label.setText("Working...")
QApplication.processEvents()           # pump the event loop
```

- Allows the progress bar to animate, labels to update, and
  the window to remain responsive during blocking computation.
- Alternative to `QThread` when the library (e.g., DrJIT) is not thread-safe.

### Dynamic Theming

```python
# In main window:
self.dark_mode = True
self.setStyleSheet(get_stylesheet(self.dark_mode))

# Toggle:
def toggle_theme(self):
    self.dark_mode = not self.dark_mode
    self.setStyleSheet(get_stylesheet(self.dark_mode))
```

- `setStyleSheet()` on `QMainWindow` cascades to all child widgets.
- QSS supports `#objectName` selectors, `.className` property selectors,
  and pseudo-states like `:hover`, `:checked`, `:focus`.

---

## 4. QSS Styling Patterns

### Object Name Selectors

```python
widget.setObjectName("primaryButton")
```

```css
QPushButton#primaryButton {
    background-color: #6366f1;
    color: white;
}
```

### Property-Based Class Selectors

```python
label.setProperty("class", "section-title")
```

```css
.section-title {
    font-size: 16px;
    font-weight: 600;
}
```

### Key QSS Pseudo-States

```css
QPushButton:hover     { }    /* mouse over */
QPushButton:checked   { }    /* toggle button is on */
QSpinBox:focus        { }    /* has keyboard focus */
QPushButton:disabled  { }    /* setEnabled(False) */
```

### Sub-Control Styling (SpinBox arrows, ComboBox dropdowns)

```css
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    background-color: #353550;
}
QSpinBox::up-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid #c0c0d0;    /* triangle pointing up */
}
```

---

## 5. Matplotlib in Qt

### Embedding a Matplotlib Figure

```python
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

fig = Figure(figsize=(6, 4))
canvas = FigureCanvasQTAgg(fig)
toolbar = NavigationToolbar2QT(canvas, parent_widget)

layout.addWidget(toolbar)
layout.addWidget(canvas)
```

### Updating Plots

```python
fig.clear()
ax = fig.add_subplot(111)
ax.stem(x, y)
ax.set_title("CIR")
fig.tight_layout()
canvas.draw()               # must call draw() to update the display
```

### Dark Theme for Matplotlib

```python
fig.patch.set_facecolor("#2d2d44")
ax.set_facecolor("#1e1e32")
ax.tick_params(colors="#9ca3af")
ax.xaxis.label.set_color("#9ca3af")
ax.yaxis.label.set_color("#9ca3af")
ax.title.set_color("#ffffff")
for spine in ax.spines.values():
    spine.set_color("#404060")
```

---

## 6. CIR Application to Waveforms

### Building a Discrete FIR from CIR

```python
tau_flat = tau.flatten()                             # delays in seconds
a_flat   = a.flatten()[:len(tau_flat)]               # complex coefficients

sample_delays = np.round(tau_flat * fs).astype(int)  # convert to samples
sample_delays -= sample_delays.min()                 # make relative

h = np.zeros(sample_delays.max() + 1, dtype=complex)
for d, c in zip(sample_delays, a_flat):
    h[d] += c

# Normalize energy
h /= np.sqrt(np.sum(np.abs(h) ** 2))

# Apply to signal
convolved = np.convolve(signal, h, mode="full")[:len(signal)]
output = np.real(convolved)
```

---

## 7. LRU Cache Pattern

```python
from collections import OrderedDict

cache: OrderedDict[tuple, Result] = OrderedDict()
MAX = 10

def get(key):
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None

def put(key, value):
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > MAX:
        cache.popitem(last=False)    # evict oldest
```

- Used to cache `SionnaResult` objects so re-running with the same
  config is instant.
- Cache key is a tuple of all config parameters (scene, positions,
  frequency, depth, antenna config).

---

## 8. Project File Map

```
gui_alternate/
├── main_window.py              Main window, tab wiring, theme toggle
├── styles/
│   └── stylesheet.py           get_stylesheet(dark_mode) → QSS string
├── backend/
│   ├── sionna_runner.py        SionnaConfig, SionnaResult, run_sionna_raytrace()
│   ├── waveform_pipeline.py    MATLAB waveform generation
│   ├── trainer.py              PyTorch training loop (CNN, ResNet1D)
│   └── dataset_generator.py    Dataset loading / spectrogram generation
├── tabs/
│   ├── waveform_tab.py         Waveform Selection tab
│   ├── channel_tab.py          Channel & Noise tab (Sionna ray tracing)
│   ├── ml_training_tab.py      ML Training tab
│   ├── inference_tab.py        Inference Results tab
│   └── evaluate_model_tab.py   Evaluate Model tab
├── widgets/
│   ├── cir_plot.py             CIR stem plot widget (Matplotlib)
│   └── scene_render_plot.py    Basic scene image widget
└── waveform_functions/         MATLAB .m files for signal generation
```
