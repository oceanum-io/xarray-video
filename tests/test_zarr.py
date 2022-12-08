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
    vid.video.to_zarr("/tmp/test.zarr", mode="w")

    test = xarray.open_dataset("/tmp/test.zarr")

    numpy.testing.assert_array_equal(vid["time"], test["time"])
    img0 = vid["video"][10].values
    img1 = test["video"][10].values
    similarity = ssim(img0, img1, channel_axis=2)
    assert similarity > 0.94


def test_write_zarr_chunks():
    vid = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test.mp4"), start_time="2022-11-01T00:00:00Z"
    )
    (nf, ny, nx, nb) = vid["video"].shape
    vid.video.to_zarr(
        "/tmp/test.zarr",
        mode="w",
        chunk_sizes={"frame": nf // 3, "pixel_y": ny // 2, "pixel_x": nx // 2},
    )

    test = xarray.open_dataset("/tmp/test.zarr", chunks={})
    assert test["video"].chunks[0][0] == nf // 3
    assert test["video"].chunks[1][0] == ny // 2
    assert test["video"].chunks[2][0] == nx // 2

    numpy.testing.assert_array_equal(vid["time"], test["time"])
    img0 = vid["video"][10].values
    img1 = test["video"][10].values
    similarity = ssim(img0, img1, channel_axis=2)
    assert similarity > 0.94


def test_append_zarr():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid1 = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test_1.mp4"))
    vid2 = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test_2.mp4"))
    vid3 = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test_3.mp4"))

    vid1.video.to_zarr("/tmp/test.zarr", mode="w")
    vid2.video.to_zarr("/tmp/test.zarr", mode="a", append_dim="frame")
    vid3.video.to_zarr("/tmp/test.zarr", mode="a", append_dim="frame")

    test = xarray.open_dataset("/tmp/test.zarr")
    img0 = vid["video"][810].values
    img1 = test["video"][810].values
    similarity = ssim(img0, img1, channel_axis=2)
    assert similarity > 0.93


def test_append_zarr_times():
    vid1 = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test_1.mp4"),
        start_time="2010-01-01T00:00:00Z",
    )
    vid2 = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test_2.mp4"),
        start_time="2010-01-01T00:02:00Z",
    )
    vid3 = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test_3.mp4"),
        start_time="2010-01-01T00:04:00Z",
    )

    vid1.video.to_zarr("/tmp/test.zarr", mode="w")
    vid2.video.to_zarr("/tmp/test.zarr", mode="a", append_dim="frame")
    vid3.video.to_zarr("/tmp/test.zarr", mode="a", append_dim="frame")

    test = xarray.open_dataset("/tmp/test.zarr")
    time = test["time"]
