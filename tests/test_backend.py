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
    container = av.open(os.path.join(HERE, "data", "ocean_test.mp4"))

    codec = container.streams[0].codec_context
    frames = container.streams[0].frames
    width = codec.width
    height = codec.height

    data = numpy.zeros((frames, height, width, 3), dtype="uint8")
    for i, frame in enumerate(container.decode(video=0)):
        data[i] = frame.to_ndarray(format="rgb24")
    return data


@pytest.fixture
def video_mkv():
    container = av.open(os.path.join(HERE, "data", "ocean_test.mkv"))

    codec = container.streams[0].codec_context
    width = codec.width
    height = codec.height

    data = []
    for i, frame in enumerate(container.decode(video=0)):
        data.append(frame.to_ndarray(format="rgb24"))
    return numpy.array(data, dtype="uint8")


def test_open_mp4(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    assert vid["video"].shape == video.shape


def test_open_mkv(video_mkv):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mkv"))
    assert vid["video"].shape == video_mkv.shape


def test_slice_frames(video):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    subset = vid["video"][210:300]
    assert len(subset) == 90
    numpy.testing.assert_array_equal(subset[0].values, video[210])


def test_slice_frames_mkv(video_mkv):
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mkv"))
    subset = vid["video"][210:300]
    assert len(subset) == 90
    numpy.testing.assert_array_equal(subset[0].values, video_mkv[210])


def test_select_time(video):
    vid = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test.mkv"), start_time="2020-01-01 00:00:00"
    )
    subset = vid.sel(time=slice("2020-01-01 00:00:00", "2020-01-01 00:00:10"))
    assert subset["time"].max() < numpy.datetime64("2020-01-01 00:00:11")
    assert len(subset["video"] == 275)
    numpy.testing.assert_array_equal(subset["video"][-1].values, video[274])


def test_subset_frames(video):
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
