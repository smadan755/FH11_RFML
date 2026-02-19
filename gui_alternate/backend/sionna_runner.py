"""
Sionna ray-tracing backend for channel simulation.

Provides a synchronous runner that loads 3D scenes, performs ray tracing,
and returns channel impulse response (CIR) data along with the scene/paths
objects needed for interactive 3D visualization via sionna-vispy.

NOTE: Sionna / DrJIT / Mitsuba use a JIT compiler that tracks computation
scopes per-thread.  All DrJIT-backed operations MUST run on the same thread
(the main Qt thread) to avoid scope-ordering crashes.  We therefore run
ray tracing synchronously and pump the Qt event loop via processEvents()
to keep the UI responsive.
"""

import os
import traceback
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Tuple, Optional, Callable

import numpy as np


# ---------------------------------------------------------------------------
# Scene map: display name -> relative path under sionna/
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
)
_SIONNA_DIR = os.path.join(_PROJECT_ROOT, "sionna")

SCENE_MAP: dict[str, str] = {
    "UT Twin 1": "austin/UT_Twin_1.xml",
    "Austin 2": "austin/Austin_2.xml",
    "Austin Downtown": "austin/Austin_Downtown.xml",
    "Austin Suburban": "austin/Austin_suburban.xml",
}

# Sensible default TX/RX positions per scene
SCENE_DEFAULTS: dict[str, dict] = {
    "UT Twin 1": {
        "tx": (20.083, 47.127, 94.0),
        "rx": (-93.897, 181.814, 0.0),
    },
    "Austin 2": {
        "tx": (-100.0, 50.0, 15.0),
        "rx": (50.0, -30.0, 1.5),
    },
    "Austin Downtown": {
        "tx": (-200.0, -100.0, 20.0),
        "rx": (-100.0, 50.0, 1.5),
    },
    "Austin Suburban": {
        "tx": (-150.0, -50.0, 10.0),
        "rx": (0.0, 80.0, 1.5),
    },
}


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------

@dataclass
class SionnaConfig:
    scene_name: str = "UT Twin 1"
    tx_position: Tuple[float, float, float] = (20.083, 47.127, 94.0)
    rx_position: Tuple[float, float, float] = (-93.897, 181.814, 0.0)
    rx_orientation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    frequency: float = 3.5e9
    max_depth: int = 5
    tx_num_rows: int = 1
    tx_num_cols: int = 1
    rx_num_rows: int = 1
    rx_num_cols: int = 1
    antenna_pattern: str = "iso"
    polarization: str = "V"
    vertical_spacing: float = 0.5
    horizontal_spacing: float = 0.5
    synthetic_array: bool = True

    @property
    def scene_path(self) -> str:
        rel = SCENE_MAP.get(self.scene_name, "austin/UT_Twin_1.xml")
        return os.path.join(_SIONNA_DIR, rel)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class SionnaResult:
    a: np.ndarray          # complex path amplitudes
    tau: np.ndarray        # delay taps in seconds
    config: SionnaConfig
    num_paths: int
    _scene: object = field(default=None, repr=False)    # for interactive preview
    _paths: object = field(default=None, repr=False)    # for interactive preview

    def get_cir_for_plot(self):
        """Return (delays_seconds, magnitudes) as 1D arrays."""
        tau_flat = self.tau.flatten()
        a_flat = self.a.flatten()[:len(tau_flat)]
        magnitudes = np.abs(a_flat)
        return tau_flat, magnitudes

    def apply_to_signal(self, signal: np.ndarray, fs: float) -> np.ndarray:
        """Convolve the CIR with a time-domain signal.

        Builds a discrete FIR filter from (delay, amplitude) pairs,
        then applies it via np.convolve.
        """
        tau_flat = self.tau.flatten()
        a_flat = self.a.flatten()[:len(tau_flat)]

        # Convert delays to sample indices
        sample_delays = np.round(tau_flat * fs).astype(int)
        sample_delays -= sample_delays.min()  # relative to earliest path

        # Build impulse response
        h_len = int(sample_delays.max()) + 1
        h = np.zeros(h_len, dtype=complex)
        for delay_samp, coeff in zip(sample_delays, a_flat):
            h[int(delay_samp)] += coeff

        # Normalize so the channel doesn't change overall power drastically
        h_energy = np.sqrt(np.sum(np.abs(h) ** 2))
        if h_energy > 0:
            h = h / h_energy

        # Convolve and keep same length as input
        convolved = np.convolve(signal, h, mode="full")[: len(signal)]
        return np.real(convolved)


# ---------------------------------------------------------------------------
# CIR cache (LRU, max 10 entries)
# ---------------------------------------------------------------------------

_cir_cache: OrderedDict[tuple, SionnaResult] = OrderedDict()
_CACHE_MAX = 10


def _cache_key(cfg: SionnaConfig) -> tuple:
    return (
        cfg.scene_name,
        cfg.tx_position,
        cfg.rx_position,
        cfg.frequency,
        cfg.max_depth,
        cfg.tx_num_rows,
        cfg.tx_num_cols,
        cfg.rx_num_rows,
        cfg.rx_num_cols,
        cfg.antenna_pattern,
        cfg.polarization,
    )


def cache_get(cfg: SionnaConfig):
    key = _cache_key(cfg)
    if key in _cir_cache:
        _cir_cache.move_to_end(key)
        return _cir_cache[key]
    return None


def cache_put(cfg: SionnaConfig, result: SionnaResult):
    key = _cache_key(cfg)
    _cir_cache[key] = result
    _cir_cache.move_to_end(key)
    while len(_cir_cache) > _CACHE_MAX:
        _cir_cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Synchronous ray-tracing runner (main-thread, DrJIT-safe)
# ---------------------------------------------------------------------------

def run_sionna_raytrace(
    config: SionnaConfig,
    on_progress: Callable[[str], None] | None = None,
) -> SionnaResult:
    """Run Sionna ray tracing synchronously on the calling thread.

    Parameters
    ----------
    config : SionnaConfig
        Scene / antenna / frequency configuration.
    on_progress : callable, optional
        ``fn(message: str)`` called at each major step so the UI can
        update a status label and pump ``processEvents()``.

    Returns
    -------
    SionnaResult
        Contains CIR data plus the scene/paths for 3-D preview.

    Raises
    ------
    Exception
        Any error from Sionna / Mitsuba / DrJIT is propagated.
    """
    def _prog(msg: str):
        if on_progress is not None:
            on_progress(msg)

    _prog("Importing Sionna (first time may take a moment)...")
    from sionna.rt import (
        load_scene,
        PlanarArray,
        Transmitter,
        Receiver,
        PathSolver,
    )

    _prog(f"Loading scene: {config.scene_name}...")
    scene = load_scene(config.scene_path)

    _prog("Configuring antenna arrays...")
    scene.tx_array = PlanarArray(
        num_rows=config.tx_num_rows,
        num_cols=config.tx_num_cols,
        vertical_spacing=config.vertical_spacing,
        horizontal_spacing=config.horizontal_spacing,
        pattern=config.antenna_pattern,
        polarization=config.polarization,
    )
    scene.rx_array = PlanarArray(
        num_rows=config.rx_num_rows,
        num_cols=config.rx_num_cols,
        vertical_spacing=config.vertical_spacing,
        horizontal_spacing=config.horizontal_spacing,
        pattern=config.antenna_pattern,
        polarization=config.polarization,
    )

    _prog("Placing TX / RX...")
    # Remove any existing TX/RX to avoid duplicate-name errors
    for name in list(scene.transmitters.keys()):
        scene.remove(name)
    for name in list(scene.receivers.keys()):
        scene.remove(name)

    tx = Transmitter(name="tx", position=list(config.tx_position))
    scene.add(tx)
    rx = Receiver(
        name="rx",
        position=list(config.rx_position),
        orientation=list(config.rx_orientation),
    )
    scene.add(rx)

    scene.frequency = config.frequency
    scene.synthetic_array = config.synthetic_array

    _prog(f"Ray tracing (max_depth={config.max_depth})...")
    path_solver = PathSolver()
    paths = path_solver(scene, max_depth=config.max_depth)

    _prog("Computing CIR...")
    a, tau = paths.cir()

    # Convert tensors to numpy
    a_np = np.array(a)
    tau_np = np.array(tau)

    return SionnaResult(
        a=a_np,
        tau=tau_np,
        config=config,
        num_paths=int(tau_np.flatten().shape[0]),
        _scene=scene,
        _paths=paths,
    )
