"""
Channel Impulse Response plotting widget.

Provides a stem plot for CIR magnitude vs delay and a
two-subplot comparison view for before/after channel application.
"""

import numpy as np
from widgets.waveform_plots import PlottingWidget, _apply_dark_style, _DARK_AXES, _DARK_GRID, _DARK_TEXT


class CIRPlot(PlottingWidget):
    """Channel Impulse Response visualization."""

    def __init__(self):
        super().__init__()
        self.refresh_button.hide()

    # ------------------------------------------------------------------
    # Stem plot: CIR magnitude vs delay
    # ------------------------------------------------------------------

    def plot_data(self, tau=None, magnitudes=None, title="Channel Impulse Response"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if tau is not None and magnitudes is not None:
            tau_us = tau * 1e6  # convert to microseconds
            markerline, stemlines, baseline = ax.stem(
                tau_us, magnitudes, linefmt="#818cf8", markerfmt="o", basefmt="#404060"
            )
            stemlines.set_linewidth(2)
            markerline.set_color("#818cf8")
            markerline.set_markersize(6)

            ax.set_xlabel("Delay (\u03bcs)")
            ax.set_ylabel("|h(\u03c4)|")
            ax.set_title(title)
            ax.grid(True, color=_DARK_GRID, alpha=0.3)
        else:
            ax.text(
                0.5, 0.5,
                "Run ray tracing to see CIR",
                ha="center", va="center", fontsize=14, color="#9ca3af",
            )

        _apply_dark_style(self.figure)
        self.figure.tight_layout()
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Before / After comparison
    # ------------------------------------------------------------------

    def plot_comparison(self, t, original, convolved, modulation=""):
        self.figure.clear()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

        ax1.plot(t, original, color="#818cf8", linewidth=0.6)
        ax1.set_title(f"Before Channel ({modulation})")
        ax1.set_ylabel("Amplitude")
        ax1.grid(True, color=_DARK_GRID, alpha=0.3)

        ax2.plot(t, convolved, color="#f97316", linewidth=0.6)
        ax2.set_title("After Channel (CIR Convolution)")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Amplitude")
        ax2.grid(True, color=_DARK_GRID, alpha=0.3)

        _apply_dark_style(self.figure)
        self.figure.tight_layout()
        self.canvas.draw()
