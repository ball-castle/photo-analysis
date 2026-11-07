"""Frequency-domain image filters used in the course experiment."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def frequency_coordinates(shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Return centered row and column frequency-bin coordinates."""
    height, width = shape
    rows = np.arange(height, dtype=np.float64) - height // 2
    columns = np.arange(width, dtype=np.float64) - width // 2
    return np.meshgrid(rows, columns, indexing="ij")


def manual_dft2(image: np.ndarray) -> np.ndarray:
    """Compute a 2-D DFT directly from the DFT definition using separability."""
    image = np.asarray(image, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("manual_dft2 expects a two-dimensional grayscale image")
    height, width = image.shape
    row_transform = np.exp(
        -2j * np.pi * np.outer(np.arange(height), np.arange(height)) / height
    )
    column_transform = np.exp(
        -2j * np.pi * np.outer(np.arange(width), np.arange(width)) / width
    )
    return row_transform @ image @ column_transform.T


def radial_filter(
    shape: tuple[int, int], d0: float, kind: str, order: int = 2
) -> np.ndarray:
    """Build an ideal, Butterworth, or Gaussian low/high-pass transfer mask.

    ``d0`` is measured in frequency bins from the centered zero-frequency bin.
    ``kind`` accepts ``ideal_lp``, ``butterworth_lp``, ``gaussian_lp``,
    ``ideal_hp``, ``butterworth_hp``, and ``gaussian_hp``.
    """
    if not np.isfinite(d0) or d0 <= 0:
        raise ValueError("d0 must be a finite positive number")
    if not isinstance(order, int) or order < 1:
        raise ValueError("order must be a positive integer")

    rows, columns = frequency_coordinates(shape)
    distance = np.hypot(rows, columns)
    if kind.endswith("_lp"):
        family = kind[:-3]
        low_pass = True
    elif kind.endswith("_hp"):
        family = kind[:-3]
        low_pass = False
    else:
        raise ValueError("kind must name a low-pass or high-pass filter")

    if family == "ideal":
        low = (distance <= d0).astype(np.float64)
    elif family == "butterworth":
        low = 1.0 / (1.0 + np.power(distance / d0, 2 * order))
    elif family == "gaussian":
        low = np.exp(-(distance**2) / (2.0 * d0**2))
    else:
        raise ValueError("filter family must be ideal, butterworth, or gaussian")

    if low_pass:
        return low
    return 1.0 - low


def high_frequency_emphasis(
    shape: tuple[int, int], d0: float, a: float = 0.5, b: float = 1.5,
    family: str = "butterworth", order: int = 2,
) -> np.ndarray:
    """Return ``a + b * H_hp`` for high-frequency emphasis enhancement."""
    if not np.isfinite(a) or not np.isfinite(b) or a < 0 or b < 0:
        raise ValueError("a and b must be finite, nonnegative numbers")
    return a + b * radial_filter(shape, d0, family + "_hp", order=order)


def gaussian_notch_reject(
    shape: tuple[int, int], centers: Iterable[tuple[int, int]], d0: float
) -> np.ndarray:
    """Build Gaussian notch rejects for conjugate peak pairs.

    Each center is one representative ``(v, u)`` pair in signed centered-bin
    coordinates: ``v`` is the row offset, ``u`` the column offset. Its
    conjugate ``(-v, -u)`` is included automatically. Supply each pair once.
    """
    if not np.isfinite(d0) or d0 <= 0:
        raise ValueError("d0 must be a finite positive number")
    rows, columns = frequency_coordinates(shape)
    transfer = np.ones(shape, dtype=np.float64)
    seen: set[tuple[int, int]] = set()
    for center in centers:
        if len(center) != 2:
            raise ValueError("each notch center must be a (v, u) pair")
        v, u = int(center[0]), int(center[1])
        canonical = min((v, u), (-v, -u))
        if canonical in seen:
            continue
        seen.add(canonical)
        d_positive = np.hypot(rows - v, columns - u)
        d_negative = np.hypot(rows + v, columns + u)
        transfer *= 1.0 - np.exp(-(d_positive**2) / (2.0 * d0**2))
        if (v, u) != (-v, -u):
            transfer *= 1.0 - np.exp(-(d_negative**2) / (2.0 * d0**2))
    return transfer


def apply_frequency_filter(image: np.ndarray, transfer: np.ndarray) -> np.ndarray:
    """Apply a centered real transfer mask and return a real-valued image."""
    image = np.asarray(image, dtype=np.float64)
    transfer = np.asarray(transfer, dtype=np.float64)
    if image.ndim != 2 or transfer.shape != image.shape:
        raise ValueError("image and transfer mask must be matching 2-D arrays")
    spectrum = np.fft.fftshift(np.fft.fft2(image))
    result = np.fft.ifft2(np.fft.ifftshift(spectrum * transfer))
    return result.real


def dominant_peak_pairs(
    image: np.ndarray, count: int = 12, min_radius: float = 6.0
) -> list[tuple[int, int, float]]:
    """Return strong conjugate spectral peaks as ``(v, u, magnitude)`` rows.

    The center/DC neighborhood is excluded. This is a proposal list for the
    interactive editor; peak choice remains a user decision.
    """
    image = np.asarray(image, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("dominant_peak_pairs expects a 2-D grayscale image")
    spectrum = np.fft.fftshift(np.fft.fft2(image - image.mean()))
    magnitude = np.abs(spectrum)
    height, width = image.shape
    rows, columns = frequency_coordinates(image.shape)
    radius = np.hypot(rows, columns)

    local_max = np.ones(image.shape, dtype=bool)
    for row_shift in (-1, 0, 1):
        for column_shift in (-1, 0, 1):
            if row_shift == 0 and column_shift == 0:
                continue
            shifted = np.roll(magnitude, (row_shift, column_shift), axis=(0, 1))
            local_max &= magnitude >= shifted
    local_max &= radius >= min_radius

    candidates = np.argwhere(local_max)
    if candidates.size == 0:
        return []

    # Keep one point from each conjugate pair; sort deterministically by strength.
    result: list[tuple[int, int, float]] = []
    for row_index, column_index in candidates:
        v = int(row_index - height // 2)
        u = int(column_index - width // 2)
        if (v, u) <= (-v, -u):
            continue
        pair_row = (-v + height // 2) % height
        pair_column = (-u + width // 2) % width
        paired_magnitude = magnitude[pair_row, pair_column]
        current_magnitude = magnitude[row_index, column_index]
        score = float(0.5 * (paired_magnitude + current_magnitude))
        result.append((v, u, score))

    result.sort(key=lambda item: (-item[2], item[0], item[1]))
    return result[:count]


def psnr(reference: np.ndarray, estimate: np.ndarray, data_range: float = 255.0) -> float:
    """Peak signal-to-noise ratio for arrays sharing the same pixel scale."""
    reference = np.asarray(reference, dtype=np.float64)
    estimate = np.asarray(estimate, dtype=np.float64)
    if reference.shape != estimate.shape:
        raise ValueError("reference and estimate must have the same shape")
    mse = float(np.mean((reference - estimate) ** 2))
    if mse == 0:
        return float("inf")
    return 10.0 * float(np.log10((data_range**2) / mse))


def to_uint8(image: np.ndarray) -> np.ndarray:
    """Clip a display/export copy to the standard grayscale pixel range."""
    return np.clip(np.rint(image), 0, 255).astype(np.uint8)
