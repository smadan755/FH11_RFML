"""
Channel simulation tab — Sionna ray-tracing channel model.

Lets users configure a 3D scene, run ray tracing to compute a channel
impulse response (CIR), interactively view the 3D scene with multipath
propagation paths (via sionna-vispy), and apply the channel to waveforms
received from the Waveform Selection tab.
"""

import os
import traceback

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDoubleSpinBox, QSpinBox, QComboBox, QGroupBox, QGridLayout,
    QTabWidget, QScrollArea, QProgressBar, QApplication,
)
from PySide6.QtCore import Qt, Signal

from backend.sionna_runner import (
    SionnaConfig, SionnaResult, run_sionna_raytrace,
    SCENE_MAP, SCENE_DEFAULTS, cache_get, cache_put,
)
from widgets.cir_plot import CIRPlot


class ChannelNoiseTab(QWidget):
    """Channel simulation tab with Sionna ray-tracing backend."""

    # Emitted after a successful ray trace
    cir_ready = Signal(object)  # SionnaResult

    def __init__(self):
        super().__init__()
        self._last_result: SionnaResult | None = None
        self._waveform_signal = None
        self._waveform_fs = None
        self._waveform_modulation = None
        self._vispy_canvas = None       # sionna-vispy Previewer (SceneCanvas)
        self.setup_ui()

    # ==================================================================
    # UI construction
    # ==================================================================

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left panel — configuration (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        left_panel = self._build_config_panel()
        scroll.setWidget(left_panel)
        layout.addWidget(scroll, 1)

        # Right panel — plots
        right_panel = self._build_plot_panel()
        layout.addWidget(right_panel, 2)

        # Load defaults for initial scene (must be after both panels are built)
        self._on_scene_changed(self.scene_combo.currentText())

    # ------------------------------------------------------------------
    # Left: config panel
    # ------------------------------------------------------------------

    def _build_config_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("card")
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(24, 24, 24, 24)
        vbox.setSpacing(16)

        # Title
        title = QLabel("Channel Simulation")
        title.setProperty("class", "section-title")
        subtitle = QLabel("Sionna ray-tracing channel model")
        subtitle.setProperty("class", "section-subtitle")
        vbox.addWidget(title)
        vbox.addWidget(subtitle)

        # Scene selection
        vbox.addWidget(self._field_label("Scene"))
        self.scene_combo = QComboBox()
        self.scene_combo.addItems(list(SCENE_MAP.keys()))
        self.scene_combo.currentTextChanged.connect(self._on_scene_changed)
        vbox.addWidget(self.scene_combo)

        # Frequency
        vbox.addWidget(self._field_label("Frequency (GHz)"))
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 100.0)
        self.freq_spin.setDecimals(2)
        self.freq_spin.setValue(3.50)
        self.freq_spin.setSingleStep(0.1)
        self.freq_spin.setSuffix(" GHz")
        vbox.addWidget(self.freq_spin)

        # Max depth
        vbox.addWidget(self._field_label("Max Ray Depth"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 10)
        self.depth_spin.setValue(5)
        vbox.addWidget(self.depth_spin)

        # TX position
        tx_group = QGroupBox("Transmitter Position")
        tx_grid = QGridLayout(tx_group)
        self.tx_x, self.tx_y, self.tx_z = self._add_xyz_row(tx_grid)
        vbox.addWidget(tx_group)

        # RX position
        rx_group = QGroupBox("Receiver Position")
        rx_grid = QGridLayout(rx_group)
        self.rx_x, self.rx_y, self.rx_z = self._add_xyz_row(rx_grid)
        vbox.addWidget(rx_group)

        # Antenna array (collapsible group)
        ant_group = QGroupBox("Antenna Array")
        ant_group.setCheckable(True)
        ant_group.setChecked(False)
        ant_grid = QGridLayout(ant_group)

        ant_grid.addWidget(QLabel("TX Rows"), 0, 0)
        self.tx_rows_spin = QSpinBox(); self.tx_rows_spin.setRange(1, 16); self.tx_rows_spin.setValue(1)
        ant_grid.addWidget(self.tx_rows_spin, 0, 1)
        ant_grid.addWidget(QLabel("TX Cols"), 0, 2)
        self.tx_cols_spin = QSpinBox(); self.tx_cols_spin.setRange(1, 16); self.tx_cols_spin.setValue(1)
        ant_grid.addWidget(self.tx_cols_spin, 0, 3)

        ant_grid.addWidget(QLabel("RX Rows"), 1, 0)
        self.rx_rows_spin = QSpinBox(); self.rx_rows_spin.setRange(1, 16); self.rx_rows_spin.setValue(1)
        ant_grid.addWidget(self.rx_rows_spin, 1, 1)
        ant_grid.addWidget(QLabel("RX Cols"), 1, 2)
        self.rx_cols_spin = QSpinBox(); self.rx_cols_spin.setRange(1, 16); self.rx_cols_spin.setValue(1)
        ant_grid.addWidget(self.rx_cols_spin, 1, 3)

        ant_grid.addWidget(QLabel("Pattern"), 2, 0)
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["iso", "dipole", "hw_dipole"])
        ant_grid.addWidget(self.pattern_combo, 2, 1)
        ant_grid.addWidget(QLabel("Polarization"), 2, 2)
        self.pol_combo = QComboBox()
        self.pol_combo.addItems(["V", "H", "cross"])
        ant_grid.addWidget(self.pol_combo, 2, 3)

        vbox.addWidget(ant_group)

        # Run button
        self.run_btn = QPushButton("Run Ray Tracing")
        self.run_btn.setObjectName("primaryButton")
        self.run_btn.clicked.connect(self.run_ray_tracing)
        vbox.addWidget(self.run_btn)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(False)
        vbox.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "section-subtitle")
        self.status_label.setWordWrap(True)
        vbox.addWidget(self.status_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #404060;")
        vbox.addWidget(sep)

        # Apply CIR button
        self.apply_btn = QPushButton("Apply CIR to Last Waveform")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_cir_to_waveform)
        vbox.addWidget(self.apply_btn)

        self.apply_info = QLabel("Generate a waveform first, then run ray tracing.")
        self.apply_info.setProperty("class", "section-subtitle")
        self.apply_info.setWordWrap(True)
        vbox.addWidget(self.apply_info)

        vbox.addStretch()

        return panel

    # ------------------------------------------------------------------
    # Right: plot panel
    # ------------------------------------------------------------------

    def _build_plot_panel(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.plot_tabs = QTabWidget()

        # --- 3D Scene View tab ---
        self.scene_tab = QWidget()
        self.scene_layout = QVBoxLayout(self.scene_tab)
        self.scene_layout.setContentsMargins(0, 0, 0, 0)

        # Hint label (shown before ray tracing)
        self.scene_hint = QLabel(
            "Run ray tracing to see the interactive 3D scene.\n"
            "You can orbit, zoom, and pan with the mouse."
        )
        self.scene_hint.setAlignment(Qt.AlignCenter)
        self.scene_hint.setStyleSheet("font-size: 14px; color: #9ca3af; padding: 40px;")
        self.scene_layout.addWidget(self.scene_hint)

        self.plot_tabs.addTab(self.scene_tab, "3D Scene")

        # --- CIR stem plot ---
        self.cir_plot = CIRPlot()
        self.plot_tabs.addTab(self.cir_plot, "CIR")

        # --- Before / After comparison ---
        self.comparison_plot = CIRPlot()
        self.plot_tabs.addTab(self.comparison_plot, "Before / After")

        # --- Path info text ---
        self.path_info_label = QLabel("Run ray tracing to see path information.")
        self.path_info_label.setProperty("class", "section-subtitle")
        self.path_info_label.setWordWrap(True)
        self.path_info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.path_info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_info_label.setStyleSheet(
            "padding: 20px; font-family: Consolas, monospace; font-size: 13px;"
        )

        path_scroll = QScrollArea()
        path_scroll.setWidgetResizable(True)
        path_scroll.setWidget(self.path_info_label)
        self.plot_tabs.addTab(path_scroll, "Path Info")

        vbox.addWidget(self.plot_tabs)
        return widget

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "field-label")
        return lbl

    def _add_xyz_row(self, grid: QGridLayout):
        row = grid.rowCount()
        spins = []
        for col, label in enumerate(("X", "Y", "Z")):
            grid.addWidget(QLabel(label), row, col * 2)
            spin = QDoubleSpinBox()
            spin.setRange(-1000.0, 1000.0)
            spin.setDecimals(2)
            spin.setSingleStep(1.0)
            grid.addWidget(spin, row, col * 2 + 1)
            spins.append(spin)
        return spins

    # ==================================================================
    # Scene changed -> update default positions
    # ==================================================================

    def _on_scene_changed(self, scene_name: str):
        defaults = SCENE_DEFAULTS.get(scene_name, {})
        tx = defaults.get("tx", (0.0, 0.0, 0.0))
        rx = defaults.get("rx", (0.0, 0.0, 0.0))
        self.tx_x.setValue(tx[0]); self.tx_y.setValue(tx[1]); self.tx_z.setValue(tx[2])
        self.rx_x.setValue(rx[0]); self.rx_y.setValue(rx[1]); self.rx_z.setValue(rx[2])

    # ==================================================================
    # Build config from UI
    # ==================================================================

    def _build_config(self) -> SionnaConfig:
        return SionnaConfig(
            scene_name=self.scene_combo.currentText(),
            tx_position=(self.tx_x.value(), self.tx_y.value(), self.tx_z.value()),
            rx_position=(self.rx_x.value(), self.rx_y.value(), self.rx_z.value()),
            frequency=self.freq_spin.value() * 1e9,
            max_depth=self.depth_spin.value(),
            tx_num_rows=self.tx_rows_spin.value(),
            tx_num_cols=self.tx_cols_spin.value(),
            rx_num_rows=self.rx_rows_spin.value(),
            rx_num_cols=self.rx_cols_spin.value(),
            antenna_pattern=self.pattern_combo.currentText(),
            polarization=self.pol_combo.currentText(),
        )

    # ==================================================================
    # Run ray tracing  (synchronous — DrJIT requires single-thread)
    # ==================================================================

    def _update_progress(self, message: str):
        """Update the status label and pump the Qt event loop."""
        self.status_label.setText(message)
        QApplication.processEvents()

    def run_ray_tracing(self):
        config = self._build_config()

        # Check cache first
        cached = cache_get(config)
        if cached is not None:
            self.status_label.setText("Loaded from cache.")
            self._on_raytrace_finished(cached)
            return

        # Disable UI while running
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting ray tracing...")
        QApplication.processEvents()

        try:
            result = run_sionna_raytrace(config, on_progress=self._update_progress)
            self._on_raytrace_finished(result)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[ChannelTab] Ray tracing error:\n{tb}")
            self.status_label.setText(f"Error — see terminal for details.")
            self.run_btn.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _on_raytrace_finished(self, result: SionnaResult):
        cache_put(result.config, result)
        self._last_result = result

        # Update CIR plot
        try:
            tau, mag = result.get_cir_for_plot()
            self.cir_plot.plot_data(
                tau, mag,
                title=f"CIR: {result.num_paths} paths \u2014 {result.config.scene_name}",
            )
        except Exception as e:
            print(f"[ChannelTab] CIR plot error: {e}")

        # Build interactive 3D preview (non-fatal if it fails)
        try:
            self._build_3d_preview(result)
        except Exception as e:
            print(f"[ChannelTab] 3D preview error: {e}")

        # Update path info
        try:
            self._update_path_info(result)
        except Exception as e:
            print(f"[ChannelTab] Path info error: {e}")

        # Enable apply button if waveform exists
        self.apply_btn.setEnabled(self._waveform_signal is not None)
        if self._waveform_signal is not None:
            self.apply_info.setText("Ready to apply CIR to waveform.")
        else:
            self.apply_info.setText("Generate a waveform on the Waveform tab first.")

        # Re-enable UI
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(
            f"Done \u2014 {result.num_paths} paths found."
        )

        self.plot_tabs.setCurrentIndex(0)  # show 3D Scene tab
        self.cir_ready.emit(result)

    # ==================================================================
    # Interactive 3D preview via sionna-vispy
    # ==================================================================

    def _save_camera_state(self) -> dict | None:
        """Snapshot the VisPy TurntableCamera so we can restore after rebuild."""
        if self._vispy_canvas is None:
            return None
        try:
            cam = self._vispy_canvas._camera
            return {
                "azimuth": cam.azimuth,
                "elevation": cam.elevation,
                "distance": cam.distance,
                "center": cam.center,
                "scale_factor": cam.scale_factor,
            }
        except Exception:
            return None

    def _restore_camera_state(self, state: dict | None):
        """Apply a previously saved camera snapshot."""
        if state is None or self._vispy_canvas is None:
            return
        try:
            cam = self._vispy_canvas._camera
            cam.azimuth = state["azimuth"]
            cam.elevation = state["elevation"]
            cam.distance = state["distance"]
            cam.center = state["center"]
            cam.scale_factor = state["scale_factor"]
        except Exception:
            pass

    def _cleanup_vispy_canvas(self):
        """Safely tear down the previous VisPy canvas, if any."""
        if self._vispy_canvas is not None:
            try:
                native = self._vispy_canvas.native
                if native is not None:
                    native.setParent(None)
                    self.scene_layout.removeWidget(native)
            except Exception:
                pass
            try:
                self._vispy_canvas.close()
            except Exception:
                pass
            self._vispy_canvas = None

    def _build_3d_preview(self, result: SionnaResult):
        """Create an interactive VisPy 3D canvas showing the scene + paths.

        The Previewer from sionna-vispy extends VisPy's SceneCanvas.
        Its .native property returns a QWidget we embed in the layout.
        Mouse controls: left-drag = orbit, scroll = zoom, right-drag = pan.

        The camera orientation is preserved across re-runs so that
        changing TX/RX and clicking "Run" doesn't reset your view.
        """
        try:
            import sionna_vispy
            from sionna_vispy.previewer import Previewer

            # Save camera orientation before destroying old canvas
            cam_state = self._save_camera_state()

            # Remove previous canvas safely
            self._cleanup_vispy_canvas()

            # Hide the hint label
            self.scene_hint.setVisible(False)

            # Create the VisPy previewer (builds meshes from the scene)
            canvas = Previewer(
                result._scene,
                resolution=(900, 600),
                fov=45,
                background="#1e1e32",
            )

            # Draw TX/RX markers and multipath rays
            canvas.plot_radio_devices()
            if result._paths is not None:
                canvas.plot_paths(result._paths)

            # Embed the native Qt widget into our layout
            self.scene_layout.addWidget(canvas.native, 1)
            self._vispy_canvas = canvas

            # Restore the camera so the view doesn't jump
            self._restore_camera_state(cam_state)

        except Exception as e:
            print(f"[ChannelTab] 3D preview error: {e}")
            self.scene_hint.setText(
                f"Could not create 3D preview:\n{e}\n\n"
                "Install sionna-vispy: pip install sionna-vispy"
            )
            self.scene_hint.setVisible(True)

    # ==================================================================
    # Path info
    # ==================================================================

    def _update_path_info(self, result: SionnaResult):
        tau_flat = result.tau.flatten()
        a_flat = np.abs(result.a.flatten()[:len(tau_flat)])
        delay_spread = tau_flat.max() - tau_flat.min()
        dominant_idx = int(np.argmax(a_flat))

        lines = [
            f"Scene:           {result.config.scene_name}",
            f"Frequency:       {result.config.frequency / 1e9:.2f} GHz",
            f"Max depth:       {result.config.max_depth}",
            f"",
            f"Number of paths: {result.num_paths}",
            f"Delay spread:    {delay_spread * 1e6:.3f} \u03bcs",
            f"Min delay:       {tau_flat.min() * 1e6:.3f} \u03bcs",
            f"Max delay:       {tau_flat.max() * 1e6:.3f} \u03bcs",
            f"",
            f"Dominant path:   index {dominant_idx}",
            f"  |a| =          {a_flat[dominant_idx]:.6f}",
            f"  \u03c4   =          {tau_flat[dominant_idx] * 1e6:.3f} \u03bcs",
            f"",
            f"TX position:     {result.config.tx_position}",
            f"RX position:     {result.config.rx_position}",
            f"",
            f"3D Controls:     Left-drag = orbit, Scroll = zoom, Right-drag = pan",
        ]
        self.path_info_label.setText("\n".join(lines))

    # ==================================================================
    # Receive waveform from WaveformSelectionTab
    # ==================================================================

    def receive_waveform(self, signal_data, fs: float, modulation: str):
        self._waveform_signal = np.array(signal_data).flatten()
        self._waveform_fs = float(fs)
        self._waveform_modulation = modulation
        if self._last_result is not None:
            self.apply_btn.setEnabled(True)
            self.apply_info.setText("Ready to apply CIR to waveform.")

    # ==================================================================
    # Apply CIR to waveform
    # ==================================================================

    def _save_channelized_waveform(self, signal: np.ndarray) -> str:
        """Save a channel-impaired waveform in the standard class-folder layout."""
        tabs_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(
            os.path.dirname(tabs_dir), "waveform_data", self._waveform_modulation
        )
        os.makedirs(output_dir, exist_ok=True)

        index = 0
        while os.path.exists(os.path.join(output_dir, f"channel_data_{index}.npy")):
            index += 1
        path = os.path.join(output_dir, f"channel_data_{index}.npy")
        np.save(path, signal)
        return path

    def apply_cir_to_waveform(self):
        if self._last_result is None or self._waveform_signal is None:
            return

        convolved = self._last_result.apply_to_signal(
            self._waveform_signal, self._waveform_fs
        )

        t = np.arange(len(self._waveform_signal)) / self._waveform_fs

        self.comparison_plot.plot_comparison(
            t, self._waveform_signal, convolved, self._waveform_modulation
        )
        save_path = self._save_channelized_waveform(convolved)
        self.apply_info.setText(
            f"Applied CIR and saved training sample: {os.path.basename(save_path)}"
        )
        self.plot_tabs.setCurrentIndex(2)  # switch to Before/After tab
