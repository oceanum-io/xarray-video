"""Tests for `xarray-video` package."""
import os
import pytest
import numpy
import xarray

import xarray_video

from skimage.metrics import structural_similarity as ssim


HERE = os.path.dirname(__file__)


def test_write_zarr():
    vid = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test.mp4"), start_time="2022-11-01T00:00:00Z"
    )
    vid.to_zarr("/tmp/test.zarr", mode="w")

    test = xarray.open_dataset("/tmp/test.zarr")

    numpy.testing.assert_array_equal(vid["time"], test["time"])
    img0 = vid["video"][10].values
    img1 = test["video"][10].values
    similarity = ssim(img0, img1, channel_axis=2)
    assert similarity > 0.94
