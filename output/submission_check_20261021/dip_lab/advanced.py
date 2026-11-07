"""Manual edge-preserving filters implemented with NumPy array operations."""

import math

import numpy as np

from .spatial import box_filter


def _gray(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image, dtype=np.float64)
    if array.ndim != 2 or not np.isfinite(array).all():
        raise ValueError("Expected a finite two-dimensional grayscale image")
    return array


def _odd_positive(value: int, label: str) -> int:
    value = int(value)
    if value < 1:
        raise ValueError(label + " must be positive")
    return value


def _shift_reflect(image: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Translate an image while reflecting values beyond its boundary."""
    source = _gray(image)
    height, width = source.shape
    mode = "symmetric" if min(source.shape) == 1 else "reflect"
    pad_y, pad_x = abs(dy), abs(dx)
    padded = np.pad(source, ((pad_y, pad_y), (pad_x, pad_x)), mode=mode)
    start_y = pad_y + dy
    start_x = pad_x + dx
    return padded[start_y : start_y + height, start_x : start_x + width]


def bilateral_filter(
    image: np.ndarray,
    radius: int = 3,
    sigma_space: float = 2.0,
    sigma_range: float = 25.0,
) -> np.ndarray:
    """Apply bilateral weighting over a square neighborhood; no library filter calls."""
    source = _gray(image)
    radius = _odd_positive(radius, "radius")
    if sigma_space <= 0 or sigma_range <= 0:
        raise ValueError("sigma_space and sigma_range must be positive")
    numerator = np.zeros_like(source)
    denominator = np.zeros_like(source)
    spatial_denominator = 2.0 * sigma_space**2
    range_denominator = 2.0 * sigma_range**2
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            neighbor = _shift_reflect(source, dy, dx)
            spatial_weight = math.exp(-(dy * dy + dx * dx) / spatial_denominator)
            range_weight = np.exp(-((neighbor - source) ** 2) / range_denominator)
            weight = spatial_weight * range_weight
            numerator += weight * neighbor
            denominator += weight
    return numerator / np.maximum(denominator, np.finfo(np.float64).tiny)


def guided_filter(
    guide: np.ndarray,
    source: np.ndarray,
    radius: int = 4,
    epsilon: float = 650.25,
) -> np.ndarray:
    """Grayscale guided filter using local linear coefficients and integral box means."""
    guide_image = _gray(guide)
    source_image = _gray(source)
    if guide_image.shape != source_image.shape:
        raise ValueError("guide and source must have equal shapes")
    radius = _odd_positive(radius, "radius")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    window = 2 * radius + 1
    mean_i = box_filter(guide_image, window)
    mean_p = box_filter(source_image, window)
    mean_ip = box_filter(guide_image * source_image, window)
    mean_ii = box_filter(guide_image * guide_image, window)
    covariance = mean_ip - mean_i * mean_p
    variance = np.maximum(mean_ii - mean_i * mean_i, 0.0)
    a = covariance / (variance + epsilon)
    b = mean_p - a * mean_i
    mean_a = box_filter(a, window)
    mean_b = box_filter(b, window)
    return mean_a * guide_image + mean_b


def non_local_means(
    image: np.ndarray,
    patch_radius: int = 2,
    search_radius: int = 5,
    h: float = 18.0,
    noise_sigma: float = 0.0,
) -> np.ndarray:
    """Approximate NLM with vectorized shifted images and integral patch distances.

    The search still examines every displacement in the specified square window.
    Patch SSD is computed as a box mean, avoiding per-pixel Python loops.
    """
    source = _gray(image)
    patch_radius = _odd_positive(patch_radius, "patch_radius")
    search_radius = _odd_positive(search_radius, "search_radius")
    if h <= 0 or noise_sigma < 0:
        raise ValueError("h must be positive and noise_sigma non-negative")
    patch_size = 2 * patch_radius + 1
    numerator = np.zeros_like(source)
    denominator = np.zeros_like(source)
    noise_bias = 2.0 * noise_sigma**2
    for dy in range(-search_radius, search_radius + 1):
        for dx in range(-search_radius, search_radius + 1):
            neighbor = _shift_reflect(source, dy, dx)
            if dy == 0 and dx == 0:
                weight = np.ones_like(source)
            else:
                distance = box_filter((source - neighbor) ** 2, patch_size)
                corrected = np.maximum(distance - noise_bias, 0.0)
                weight = np.exp(-corrected / (h * h))
            numerator += weight * neighbor
            denominator += weight
    return numerator / np.maximum(denominator, np.finfo(np.float64).tiny)
