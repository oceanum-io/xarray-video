#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xarray-video` package."""
import os
import pytest
import numpy
import xarray

import xarray_video

HERE = os.path.dirname(__file__)


def test_video_plot():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid["video"][10].video.plot()


def test_video_play():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid["video"].video.play(figsize=(12, 10), start_time="2010-01-01")


def test_dataset_to_file():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid.video.to_video("/tmp/dataset.mp4")
