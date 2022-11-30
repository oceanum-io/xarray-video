import os
import sys
import pytest
import numpy
import numcodecs
import zarr
import cv2

import xarray_video

# from xarray_video.codecs import mp4v
HERE = os.path.dirname(__file__)
# sys.path.insert(0, os.path.join(HERE, ".."))

compressor = numcodecs.registry.get_codec(dict(id="mp4v"))


@pytest.fixture
def video():
    """Connection fixture"""
    video = cv2.VideoCapture(os.path.join(HERE, "data", "ocean_test.mp4"))

    frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    data = numpy.zeros((frames, height, width, 3), dtype="uint8")
    i = 0
    while True:
        ok, image = video.read()
        if not ok:
            break
        data[i] = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        i += 1
    video.release()
    return data


def test_zarr_write(video):
    nf, ny, nx, nb = video.shape
    z1 = zarr.open(
        "/tmp/test.zarr",
        mode="w",
        shape=(nf, ny, nx, nb),
        chunks=(nf, ny, nx, nb),
        dtype="uint8",
        compressor=compressor,
    )
    z1[:] = video
    z2 = zarr.open("/tmp/test.zarr", mode="r")
    test = z2[:]
