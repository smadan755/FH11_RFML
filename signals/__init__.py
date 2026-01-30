# FH11_RFML/signals/__init__.py

"""
rfml.signals: per-family waveform generators.

Each generator follows the same interface:
    generate_<family>(spec: SignalSpec) -> Waveform
"""

from .psk import generate_psk
from .qam import generate_qam
from .ofdm import generate_ofdm

## needed later
# from .gfsk import generate_gfsk
# from .dsss_oqpsk import generate_dsss_oqpsk
# from .css_lora import generate_css_lora

__all__ = [
    "generate_psk",
    "generate_qam",
    "generate_ofdm",
    # "generate_gfsk",
    # "generate_dsss_oqpsk",
    # "generate_css_lora",
]
