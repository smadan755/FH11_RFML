# augmentation/__init__.py
"""
RF Signal Augmentation Module

Provides composable augmentation blocks for RF signal machine learning.
"""

from .augmentation import (
    AugmentationBlock,
    AugmentationPipeline,
    AWGNAugmentation,
    ScalarAmplitudeAndPhaseShift, 
)

__all__ = [
    "AugmentationBlock",
    "AugmentationPipeline",
    "AWGNAugmentation",
    "ScalarAmplitudeAndPhaseShift",
]
