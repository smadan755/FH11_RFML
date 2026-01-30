# FH11_RFML/__init__.py

"""
rfml: RF Machine Learning waveform generation + channel + dataset utilities.

This package exposes the most commonly used public APIs (specs + helpers)
so scripts can import from `rfml` cleanly.
"""

from specs import SignalSpec, ChannelSpec, MixSpec, Waveform

__all__ = [
    "SignalSpec",
    "ChannelSpec",
    "MixSpec",
    "Waveform",
]
