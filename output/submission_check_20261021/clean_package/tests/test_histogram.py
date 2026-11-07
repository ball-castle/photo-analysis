import numpy as np

from dip_lab.histogram import (
    equalize_histogram,
    gray_histogram,
    make_bimodal_target,
    match_histogram,
)


def test_gray_histogram_counts_every_uint8_value():
    image = np.array([[0, 0, 4], [255, 4, 4]], dtype=np.uint8)
    histogram = gray_histogram(image)

    assert histogram.shape == (256,)
    assert histogram.dtype.kind in "iu"
    assert histogram[0] == 2
    assert histogram[4] == 3
    assert histogram[255] == 1
    assert histogram.sum() == image.size


def test_equalization_keeps_a_constant_image_constant():
    image = np.full((4, 5), 73, dtype=np.uint8)

    result = equalize_histogram(image)

    np.testing.assert_array_equal(result, image)


def test_equalization_spreads_two_levels_and_preserves_shape():
    image = np.array([[20, 20, 80], [80, 80, 80]], dtype=np.uint8)

    result = equalize_histogram(image)

    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert result.min() == 0
    assert result.max() == 255


def test_histogram_matching_maps_ordered_source_levels_to_target():
    source = np.array([[0, 0, 0, 255]], dtype=np.uint8)
    target = np.array([[40, 40, 40, 200]], dtype=np.uint8)

    result = match_histogram(source, target)

    assert result.shape == source.shape
    assert set(np.unique(result)) == {40, 200}


def test_bimodal_target_is_normalized_and_has_two_peaks():
    target = make_bimodal_target(peak1=65, peak2=185, sigma=9)

    assert target.shape == (256,)
    assert np.isclose(target.sum(), 1.0)
    assert target.argmax() in range(60, 70) or target.argmax() in range(180, 190)
    assert target[65] > target[120]
    assert target[185] > target[120]
