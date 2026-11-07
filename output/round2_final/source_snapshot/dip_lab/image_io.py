"""Pillow-only grayscale loading and aspect-preserving square preparation."""

from pathlib import Path

import numpy as np
from PIL import Image


def load_gray_square(path, size: int = 512) -> np.ndarray:
    """Load a photo, center-crop to a square, resize without geometric stretching."""
    if size < 1:
        raise ValueError("size must be positive")
    with Image.open(Path(path)) as opened:
        image = opened.convert("L")
        width, height = image.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        return np.asarray(image, dtype=np.uint8)
