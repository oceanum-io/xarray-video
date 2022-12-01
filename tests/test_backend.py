#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xarray-video` package."""
import os
import pytest
import numpy
import av

import xarray_video

HERE = os.path.dirname(__file__)


@pytest.fixture
def video():
    """Connection fixture"""
    container = av.open(os.path.join(HERE, "data", "ocean_test.mp4"))

    codec = container.streams[0].codec_context
    frames = container.streams[0].frames
    width = codec.width
    height = codec.height

    data = numpy.zeros((frames, height, width, 3), dtype="uint8")
    for i, frame in enumerate(container.decode(video=0)):
        data[i] = frame.to_ndarray(format="rgb24")
    return data


def test_open_video(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    assert vid["video"].shape == video.shape


def test_slice_time(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    subset = vid["video"][10:100]
    assert len(subset) == 90
    numpy.testing.assert_array_equal(subset[0].values, video[10])


def test_time_step(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    subset = vid["video"][::10]
    assert len(subset) == 98
    numpy.testing.assert_array_equal(subset[1].values, video[10])


def test_slice_frame(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    subset = vid["video"][:, 100:200, 100:200]
    assert subset.shape == (
        977,
        100,
        100,
        3,
    )
    numpy.testing.assert_array_equal(subset[101].values, video[101, 100:200, 100:200])


def test_get_pixel(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    subset = vid["video"][:, 200, 200]
    numpy.testing.assert_array_equal(subset.values, video[:, 200, 200])
