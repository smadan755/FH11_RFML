# augmentation/__init__.py
"""
RF Signal Augmentation Module

Provides composable augmentation blocks for RF signal machine learning.
"""

from .augmentation import (
    AugmentationBlock,
    AugmentationPipeline,
    AWGNAugmentation,
)

__all__ = [
    "AugmentationBlock",
    "AugmentationPipeline",
    "AWGNAugmentation",
]
