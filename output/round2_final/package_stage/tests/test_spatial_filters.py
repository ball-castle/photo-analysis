import numpy as np

from dip_lab.noise import add_gaussian_noise, add_mixed_noise, add_salt_pepper_noise
from dip_lab.spatial import (
    box_filter,
    gaussian_filter,
    laplacian_response,
    mean_filter,
    median_filter,
    prewitt_response,
    roberts_response,
    sobel_response,
)
from dip_lab.advanced import bilateral_filter, guided_filter, non_local_means


def test_box_filter_preserves_constant_for_large_window_and_one_pixel():
    one_pixel = np.array([[17.0]])
    constant = np.full((3, 4), 17.0)

    np.testing.assert_allclose(box_filter(one_pixel, 7), one_pixel)
    np.testing.assert_allclose(box_filter(constant, 7), constant)


def test_box_filter_reflects_edges_without_repeating_edge_pixels():
    image = np.array([[1.0, 2.0], [3.0, 4.0]])

    result = box_filter(image, 3)

    assert np.isclose(result[0, 0], 3.0)


def test_mean_and_gaussian_filters_preserve_constant_boundaries():
    image = np.full((2, 3), 91.0)

    np.testing.assert_allclose(mean_filter(image, 5), image)
    np.testing.assert_allclose(gaussian_filter(image, 7, 1.5), image, atol=1e-10)


def test_median_filter_removes_center_impulse_and_handles_tiny_images():
    image = np.zeros((3, 3), dtype=np.uint8)
    image[1, 1] = 255

    result = median_filter(image, 3)
    tiny = median_filter(np.array([[12]], dtype=np.uint8), 7)

    assert result[1, 1] == 0
    np.testing.assert_array_equal(tiny, np.array([[12]], dtype=np.uint8))


def test_laplacian_sign_for_bright_impulse_supports_additive_sharpening():
    image = np.zeros((5, 5), dtype=np.float64)
    image[2, 2] = 100

    result = laplacian_response(image)

    assert result[2, 2] > 0
    assert result[2, 1] < 0


def test_edge_operators_return_finite_arrays_with_original_shape():
    image = np.arange(25, dtype=np.float64).reshape(5, 5)

    for response in (roberts_response, sobel_response, prewitt_response):
        result = response(image)
        assert result.shape == image.shape
        assert np.isfinite(result).all()


def test_zero_noise_is_exact_and_seed_is_reproducible():
    image = np.array([[0, 40], [255, 90]], dtype=np.uint8)

    np.testing.assert_array_equal(add_gaussian_noise(image, sigma=0, seed=7), image)
    np.testing.assert_array_equal(add_salt_pepper_noise(image, density=0, seed=7), image)
    np.testing.assert_array_equal(
        add_mixed_noise(image, gaussian_sigma=0, salt_pepper_density=0, seed=7), image
    )
    np.testing.assert_array_equal(
        add_gaussian_noise(image, sigma=18, seed=19),
        add_gaussian_noise(image, sigma=18, seed=19),
    )


def test_edge_preserving_filters_keep_constant_input_and_support_small_arrays():
    image = np.full((1, 2), 80.0)

    bilateral = bilateral_filter(image, radius=2, sigma_space=1.0, sigma_range=20.0)
    guided = guided_filter(image, image, radius=2, epsilon=1e-3)
    nlm = non_local_means(image, patch_radius=1, search_radius=2, h=10.0)

    for result in (bilateral, guided, nlm):
        assert result.shape == image.shape
        assert np.isfinite(result).all()
        np.testing.assert_allclose(result, image, atol=1e-6)
