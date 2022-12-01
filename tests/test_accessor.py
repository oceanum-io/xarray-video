#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xarray-video` package."""
import os
import pytest
import numpy
import xarray
import matplotlib.pyplot as plt

import xarray_video

HERE = os.path.dirname(__file__)


def test_video_plot():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid["video"][10].video.plot()
    plt.show()


def test_video_to_zarr():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid["video"].encoding = {}
    vid.video.to_zarr("/tmp/test.zarr", mode="w")

    test = xarray.open_dataset("/tmp/test.zarr")
    assert test["video"].encoding["compressor"].codec_id == "mp4"
