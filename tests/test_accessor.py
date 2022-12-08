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
    vid["video"].video.play(figsize=(12, 10))


def test_video_play_time():
    vid = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test.mp4"), start_time="2010-01-01"
    )
    vid["video"].video.play(figsize=(12, 10), repeat=False)


def test_video_play_partial():
    vid = xarray_video.open_video(
        os.path.join(HERE, "data", "ocean_test.mkv"), start_time="2010-01-01"
    )
    vid["video"][300::4].video.play(figsize=(12, 10), repeat=False)


def test_dataset_to_file():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    vid.video.to_video("/tmp/dataset.mp4")
