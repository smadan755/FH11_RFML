"""
3D scene render visualization widget.

Displays a rendered image of the Sionna scene with multipath
propagation paths overlaid. Supports re-rendering from different
camera angles.
"""

import numpy as np
from widgets.waveform_plots import PlottingWidget, _apply_dark_style, _DARK_AXES, _DARK_GRID, _DARK_TEXT


class SceneRenderPlot(PlottingWidget):
    """Displays a rendered 3D scene image with propagation paths."""

    def __init__(self):
        super().__init__()
        self.refresh_button.hide()

    def plot_data(self, image: np.ndarray = None, title: str = "3D Scene View"):
        """Display a rendered scene image (H, W, 3) uint8 array."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if image is not None and image.size > 0:
            ax.imshow(image)
            ax.set_title(title)
            ax.axis("off")
        else:
            ax.text(
                0.5, 0.5,
                "Run ray tracing to see the 3D scene\nwith multipath propagation paths",
                ha="center", va="center", fontsize=14, color="#9ca3af",
                multialignment="center",
            )

        _apply_dark_style(self.figure)
        self.figure.tight_layout()
        self.canvas.draw()
