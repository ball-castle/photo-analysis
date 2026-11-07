"""Reproducible Gaussian, impulse, and mixed noise generation."""

import numpy as np


def _gray_u8(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim != 2 or not np.isfinite(array).all():
        raise ValueError("Expected a finite two-dimensional grayscale image")
    return np.clip(np.rint(array), 0, 255).astype(np.uint8)


def add_gaussian_noise(image: np.ndarray, sigma: float = 18.0, seed: int = 20261008) -> np.ndarray:
    """Add zero-mean Gaussian noise, clip to display range, and return uint8."""
    source = _gray_u8(image)
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    if sigma == 0:
        return source.copy()
    rng = np.random.default_rng(seed)
    noisy = source.astype(np.float64) + rng.normal(0.0, sigma, size=source.shape)
    return np.clip(np.rint(noisy), 0, 255).astype(np.uint8)


def add_salt_pepper_noise(
    image: np.ndarray,
    density: float = 0.04,
    seed: int = 20261008,
) -> np.ndarray:
    """Replace a reproducible fraction of pixels with 0 or 255."""
    source = _gray_u8(image)
    if not 0.0 <= density <= 1.0:
        raise ValueError("density must be in [0, 1]")
    if density == 0:
        return source.copy()
    rng = np.random.default_rng(seed)
    draw = rng.random(source.shape)
    result = source.copy()
    result[draw < density / 2.0] = 0
    result[(draw >= density / 2.0) & (draw < density)] = 255
    return result


def add_mixed_noise(
    image: np.ndarray,
    gaussian_sigma: float = 12.0,
    salt_pepper_density: float = 0.02,
    seed: int = 20261008,
) -> np.ndarray:
    """Add Gaussian and salt-pepper noise from independent fixed RNG streams."""
    source = _gray_u8(image)
    if gaussian_sigma < 0 or not 0.0 <= salt_pepper_density <= 1.0:
        raise ValueError("Noise parameters are outside their valid ranges")
    if gaussian_sigma == 0 and salt_pepper_density == 0:
        return source.copy()
    rng = np.random.default_rng(seed)
    noisy = source.astype(np.float64)
    if gaussian_sigma > 0:
        noisy += rng.normal(0.0, gaussian_sigma, size=source.shape)
    result = np.clip(np.rint(noisy), 0, 255).astype(np.uint8)
    if salt_pepper_density > 0:
        draw = rng.random(source.shape)
        result[draw < salt_pepper_density / 2.0] = 0
        result[(draw >= salt_pepper_density / 2.0) & (draw < salt_pepper_density)] = 255
    return result
