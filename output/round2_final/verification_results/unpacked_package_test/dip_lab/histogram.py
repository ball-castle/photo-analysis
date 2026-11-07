"""Hand-written grayscale histogram operations for uint8 images."""

from typing import Union

import numpy as np


ArrayLike = Union[np.ndarray, list]


def _gray_u8(image: ArrayLike) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim != 2:
        raise ValueError("Expected a two-dimensional grayscale image")
    if not np.isfinite(array).all():
        raise ValueError("Image values must be finite")
    return np.clip(np.rint(array), 0, 255).astype(np.uint8)


def gray_histogram(image: ArrayLike) -> np.ndarray:
    """Count the occurrences of gray levels 0..255 without image libraries."""
    pixels = _gray_u8(image).ravel()
    return np.bincount(pixels, minlength=256).astype(np.int64, copy=False)


def equalize_histogram(image: ArrayLike) -> np.ndarray:
    """Apply discrete CDF equalization, mapping the first occupied CDF to zero."""
    source = _gray_u8(image)
    counts = gray_histogram(source)
    occupied = np.flatnonzero(counts)
    if occupied.size <= 1:
        return source.copy()

    cdf = counts.cumsum(dtype=np.float64) / float(source.size)
    cdf_min = cdf[occupied[0]]
    denominator = 1.0 - cdf_min
    if denominator <= np.finfo(np.float64).eps:
        return source.copy()
    lut = np.clip(np.rint((cdf - cdf_min) * (255.0 / denominator)), 0, 255)
    return lut[source].astype(np.uint8)


def _target_probability(target: ArrayLike) -> np.ndarray:
    values = np.asarray(target)
    if values.ndim == 2:
        counts = gray_histogram(values)
        return counts.astype(np.float64) / max(float(counts.sum()), 1.0)
    if values.ndim != 1 or values.size != 256:
        raise ValueError("Target must be a grayscale image or a 256-entry histogram")
    probability = values.astype(np.float64)
    if not np.isfinite(probability).all() or np.any(probability < 0):
        raise ValueError("Target histogram must contain finite, non-negative values")
    total = float(probability.sum())
    if total <= 0:
        raise ValueError("Target histogram must have positive mass")
    return probability / total


def match_histogram(image: ArrayLike, target: ArrayLike) -> np.ndarray:
    """Map source CDF values to the closest target CDF gray level."""
    source = _gray_u8(image)
    source_counts = gray_histogram(source)
    if np.count_nonzero(source_counts) <= 1:
        return source.copy()

    source_cdf = source_counts.cumsum(dtype=np.float64) / float(source.size)
    target_cdf = np.cumsum(_target_probability(target), dtype=np.float64)
    target_cdf[-1] = 1.0
    lut = np.searchsorted(target_cdf, source_cdf, side="left")
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return lut[source]


def make_bimodal_target(
    peak1: float = 65.0,
    peak2: float = 185.0,
    sigma: float = 12.0,
    weight1: float = 0.5,
) -> np.ndarray:
    """Build a normalized two-Gaussian target distribution over gray levels."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if not 0.0 <= weight1 <= 1.0:
        raise ValueError("weight1 must be in [0, 1]")
    levels = np.arange(256, dtype=np.float64)
    component1 = np.exp(-0.5 * ((levels - peak1) / sigma) ** 2)
    component2 = np.exp(-0.5 * ((levels - peak2) / sigma) ** 2)
    target = weight1 * component1 + (1.0 - weight1) * component2
    return target / target.sum()
