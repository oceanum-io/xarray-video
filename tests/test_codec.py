import os
import sys
import pytest
import numpy
import numcodecs
import zarr
import av
from skimage.metrics import structural_similarity as ssim

import xarray_video

HERE = os.path.dirname(__file__)

compressor = numcodecs.registry.get_codec(dict(id="h264"))


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
    numpy.testing.assert_array_equal(z1[10], test[10])
    # Compressed version not identical because using a different codec
    similarity = ssim(video[10], test[10], channel_axis=2)
    assert similarity > 0.94
