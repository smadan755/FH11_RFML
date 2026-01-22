"""
RF Signal Augmentation Pipeline for Machine Learning
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import numpy as np


class AugmentationBlock(ABC):
    """Base class for all augmentation blocks"""

    @abstractmethod
    def apply(self, signal: np.ndarray, fs: float, **kwargs) -> np.ndarray:
        """
        Apply augmentation to a signal.

        Args:
            signal: Input signal (real passband from MATLAB generator)
            fs: Sample rate in Hz
            **kwargs: Additional parameters

        Returns:
            Augmented signal
        """
        pass

    def __call__(self, signal: np.ndarray, fs: float, **kwargs) -> np.ndarray:
        """Allow calling block as a function"""
        return self.apply(signal, fs, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class AugmentationPipeline:
    """class to chain multiple augmentation blocks together"""

    def __init__(self, blocks: Optional[List[AugmentationBlock]] = None):
        self.blocks = blocks if blocks is not None else []

    def add(self, block: AugmentationBlock) -> 'AugmentationPipeline':
        self.blocks.append(block)
        return self

    def apply(self, signal: np.ndarray, fs: float, **kwargs) -> np.ndarray:
        """
        Apply all blocks in sequence.

        Returns augmented signal after all blocks
        """
        result = signal.copy()
        for block in self.blocks:
            result = block(result, fs, **kwargs)
        return result

    def __call__(self, signal: np.ndarray, fs: float, **kwargs) -> np.ndarray:
        return self.apply(signal, fs, **kwargs)

    def __repr__(self) -> str:
        block_names = [repr(b) for b in self.blocks]
        return f"AugmentationPipeline([{', '.join(block_names)}])"


# Additive White Gaussian Noise
class AWGNAugmentation(AugmentationBlock):
    def __init__(
        self,
        snr_db: float = 20.0,
        snr_range: Optional[Tuple[float, float]] = None,
        seed: Optional[int] = None
    ):
        """
            snr_db: Fixed SNR in dB (used if snr_range is None)
            snr_range: Optional (min, max) SNR range for random selection
        """
        self.snr_db = snr_db
        self.snr_range = snr_range
        self.rng = np.random.default_rng(seed)

    def apply(self, signal: np.ndarray, _fs: float, **_kwargs) -> np.ndarray:
        """
        Add AWGN to the signal.

        Args:
            signal: Input signal (real or complex)
            _fs: Sample rate (not used for amplitude augmentation)

        Returns:
            Signal with added noise at specified SNR
        """
        # Determine SNR to use
        if self.snr_range is not None:
            snr_db = self.rng.uniform(self.snr_range[0], self.snr_range[1])
        else:
            snr_db = self.snr_db
        
        sig_power = np.mean(np.abs(signal) ** 2)

        snr_linear = 10 ** (snr_db / 10)
        noise_power = sig_power / snr_linear

        # Generate noise based on signal type
        if np.iscomplexobj(signal):
            # Complex: noise power split between I and Q
            noise_std = np.sqrt(noise_power / 2)
            noise = (self.rng.normal(0, noise_std, signal.shape) +
                     1j * self.rng.normal(0, noise_std, signal.shape))
        else:
            noise_std = np.sqrt(noise_power)
            noise = self.rng.normal(0, noise_std, signal.shape)

        return signal + noise

    def __repr__(self) -> str:
        if self.snr_range:
            return f"AWGNAugmentation(snr_range={self.snr_range})"
        return f"AWGNAugmentation(snr_db={self.snr_db})"

