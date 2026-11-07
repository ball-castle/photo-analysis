import numpy as np
from PIL import Image

from dip_lab.image_io import load_gray_square
from dip_lab.metrics import psnr, ssim


def test_square_preparation_center_crops_instead_of_stretching(tmp_path):
    image = np.tile(np.array([0, 10, 20, 30], dtype=np.uint8), (2, 1))
    path = tmp_path / "wide.png"
    Image.fromarray(image, mode="L").save(path)

    result = load_gray_square(path, size=2)

    assert result.shape == (2, 2)
    np.testing.assert_array_equal(result, np.array([[10, 20], [10, 20]], dtype=np.uint8))


def test_metrics_return_perfect_scores_for_identical_reference():
    image = np.arange(64, dtype=np.uint8).reshape(8, 8)

    assert np.isinf(psnr(image, image))
    assert np.isclose(ssim(image, image), 1.0)


def test_ssim_rejects_images_smaller_than_its_valid_window():
    image = np.zeros((6, 8), dtype=np.uint8)

    try:
        ssim(image, image)
    except ValueError as error:
        assert "at least 7" in str(error)
    else:
        raise AssertionError("SSIM should reject a dimension smaller than seven")
