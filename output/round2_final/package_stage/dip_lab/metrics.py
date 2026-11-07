"""Quality metrics for denoising with an explicitly available clean reference."""

import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def psnr(reference: np.ndarray, estimate: np.ndarray) -> float:
    """PSNR on the shared 0..255 grayscale scale."""
    ref = np.asarray(reference, dtype=np.float64)
    est = np.asarray(estimate, dtype=np.float64)
    if ref.shape != est.shape or ref.ndim != 2:
        raise ValueError("reference and estimate must be same-shaped grayscale images")
    if np.array_equal(ref, est):
        return float("inf")
    return float(peak_signal_noise_ratio(ref, est, data_range=255.0))


def ssim(reference: np.ndarray, estimate: np.ndarray) -> float:
    """SSIM using scikit-image's validated metric implementation."""
    ref = np.asarray(reference, dtype=np.float64)
    est = np.asarray(estimate, dtype=np.float64)
    if ref.shape != est.shape or ref.ndim != 2:
        raise ValueError("reference and estimate must be same-shaped grayscale images")
    if min(ref.shape) < 7:
        raise ValueError("SSIM requires both dimensions to be at least 7 pixels")
    return float(structural_similarity(ref, est, data_range=255.0, channel_axis=None))


def compare(reference: np.ndarray, estimate: np.ndarray) -> dict:
    return {"psnr_db": psnr(reference, estimate), "ssim": ssim(reference, estimate)}
