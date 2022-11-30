#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xarray-video` package."""
import os
import pytest

import xarray_video

HERE = os.path.dirname(__file__)


def test_open_video():
    vid = xarray_video.open_video(os.path.join(HERE, "data", "ocean_test.mp4"))
    assert vid
