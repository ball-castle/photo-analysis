"""Manual spatial-domain filters and classical edge operators."""

from typing import Optional

import numpy as np


def _float_gray(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError("Expected a two-dimensional grayscale image")
    if not np.isfinite(array).all():
        raise ValueError("Image values must be finite")
    return array


def _check_odd_size(size: int) -> int:
    size = int(size)
    if size < 1 or size % 2 == 0:
        raise ValueError("Window size must be a positive odd integer")
    return size


def _pad_mode(image: np.ndarray) -> str:
    return "symmetric" if min(image.shape) == 1 else "reflect"


def correlate2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Correlate a grayscale image with an odd-sized kernel using NumPy only."""
    source = _float_gray(image)
    weights = np.asarray(kernel, dtype=np.float64)
    if weights.ndim != 2 or any(size % 2 == 0 for size in weights.shape):
        raise ValueError("Kernel dimensions must be odd")
    row_radius, col_radius = weights.shape[0] // 2, weights.shape[1] // 2
    padded = np.pad(
        source,
        ((row_radius, row_radius), (col_radius, col_radius)),
        mode=_pad_mode(source),
    )
    result = np.zeros_like(source)
    height, width = source.shape
    for row in range(weights.shape[0]):
        for col in range(weights.shape[1]):
            result += weights[row, col] * padded[row : row + height, col : col + width]
    return result


def box_filter(image: np.ndarray, size: int) -> np.ndarray:
    """Return local box means using an integral image and reflected borders."""
    source = _float_gray(image)
    size = _check_odd_size(size)
    radius = size // 2
    padded = np.pad(source, ((radius, radius), (radius, radius)), mode=_pad_mode(source))
    integral = np.pad(padded.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))
    height, width = source.shape
    bottom_right = integral[size : size + height, size : size + width]
    top_right = integral[:height, size : size + width]
    bottom_left = integral[size : size + height, :width]
    top_left = integral[:height, :width]
    return (bottom_right - top_right - bottom_left + top_left) / float(size * size)


def mean_filter(
    image: np.ndarray,
    size: int = 3,
    weights: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply a uniform or caller-supplied normalized spatial mean kernel."""
    source = _float_gray(image)
    if weights is None:
        return box_filter(source, size)
    kernel = np.asarray(weights, dtype=np.float64)
    if kernel.ndim != 2 or any(dimension % 2 == 0 for dimension in kernel.shape):
        raise ValueError("weights must be a two-dimensional odd-sized matrix")
    total = float(kernel.sum())
    if not np.isfinite(kernel).all() or abs(total) <= np.finfo(np.float64).eps:
        raise ValueError("weights must have a finite, non-zero sum")
    return correlate2d(source, kernel / total)


def median_filter(image: np.ndarray, size: int = 3) -> np.ndarray:
    """Apply a sliding-window median with reflected borders."""
    source = _float_gray(image)
    size = _check_odd_size(size)
    radius = size // 2
    padded = np.pad(source, ((radius, radius), (radius, radius)), mode=_pad_mode(source))
    windows = np.lib.stride_tricks.sliding_window_view(padded, (size, size))
    return np.median(windows, axis=(-2, -1))


def _filter_axis(image: np.ndarray, kernel: np.ndarray, axis: int) -> np.ndarray:
    radius = kernel.size // 2
    pad_width = ((radius, radius), (0, 0)) if axis == 0 else ((0, 0), (radius, radius))
    padded = np.pad(image, pad_width, mode=_pad_mode(image))
    result = np.zeros_like(image)
    height, width = image.shape
    for index, weight in enumerate(kernel):
        if axis == 0:
            result += weight * padded[index : index + height, :]
        else:
            result += weight * padded[:, index : index + width]
    return result


def gaussian_filter(image: np.ndarray, size: int = 5, sigma: float = 1.0) -> np.ndarray:
    """Apply a normalized separable Gaussian kernel without a library filter."""
    source = _float_gray(image)
    size = _check_odd_size(size)
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    coordinates = np.arange(-(size // 2), size // 2 + 1, dtype=np.float64)
    kernel = np.exp(-(coordinates**2) / (2.0 * sigma**2))
    kernel /= kernel.sum()
    return _filter_axis(_filter_axis(source, kernel, axis=1), kernel, axis=0)


def roberts_components(image: np.ndarray) -> tuple:
    """Return two signed Roberts cross responses using reflected bottom/right edges."""
    source = _float_gray(image)
    height, width = source.shape
    padded = np.pad(source, ((0, 1), (0, 1)), mode=_pad_mode(source))
    gx = padded[:height, :width] - padded[1 : height + 1, 1 : width + 1]
    gy = padded[:height, 1 : width + 1] - padded[1 : height + 1, :width]
    return gx, gy


def _gradient_components(image: np.ndarray, kind: str) -> tuple:
    if kind == "sobel":
        horizontal = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
        vertical = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
    elif kind == "prewitt":
        horizontal = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float64)
        vertical = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float64)
    else:
        raise ValueError("kind must be 'sobel' or 'prewitt'")
    return correlate2d(image, horizontal), correlate2d(image, vertical)


def _magnitude(components: tuple) -> np.ndarray:
    gx, gy = components
    return np.hypot(gx, gy)


def roberts_response(image: np.ndarray) -> np.ndarray:
    return _magnitude(roberts_components(image))


def sobel_components(image: np.ndarray) -> tuple:
    return _gradient_components(image, "sobel")


def sobel_response(image: np.ndarray) -> np.ndarray:
    return _magnitude(sobel_components(image))


def prewitt_components(image: np.ndarray) -> tuple:
    return _gradient_components(image, "prewitt")


def prewitt_response(image: np.ndarray) -> np.ndarray:
    return _magnitude(prewitt_components(image))


def laplacian_response(image: np.ndarray) -> np.ndarray:
    """Signed four-neighbor Laplacian with a positive center coefficient."""
    kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float64)
    return correlate2d(image, kernel)


def stretch_to_u8(image: np.ndarray) -> np.ndarray:
    """Linearly stretch finite values to [0, 255], returning zeros if constant."""
    source = _float_gray(image)
    low, high = float(source.min()), float(source.max())
    if high - low <= np.finfo(np.float64).eps:
        return np.zeros(source.shape, dtype=np.uint8)
    return np.clip(np.rint((source - low) * (255.0 / (high - low))), 0, 255).astype(np.uint8)


def laplacian_variants(image: np.ndarray) -> dict:
    """Return absolute, stretched, additive-clipped, and raw signed Laplacian results."""
    source = _float_gray(image)
    response = laplacian_response(source)
    return {
        "response": response,
        "absolute": np.clip(np.rint(np.abs(response)), 0, 255).astype(np.uint8),
        "stretched": stretch_to_u8(response),
        "overlay": np.clip(np.rint(source + response), 0, 255).astype(np.uint8),
    }


def edge_sharpen(image: np.ndarray, kind: str, amount: float = 0.15) -> np.ndarray:
    """Create a conservative edge-mask overlay; signed Laplacian is preferred for detail."""
    source = _float_gray(image)
    if kind == "roberts":
        response = roberts_response(source)
    elif kind == "sobel":
        response = sobel_response(source)
    elif kind == "prewitt":
        response = prewitt_response(source)
    else:
        raise ValueError("kind must be roberts, sobel, or prewitt")
    # Centering the positive magnitude limits a global brightness lift while retaining edges.
    detail = response - box_filter(response, 3)
    return np.clip(source + amount * detail, 0.0, 255.0)
