###Video backend for xarray based on the xarray rasterio backend


import os
import warnings

import numpy as np
import numcodecs
import av

from xarray import DataArray, Dataset
from xarray.core import indexing
from xarray.core.utils import is_scalar
from xarray.backends.common import BackendArray
from xarray.backends.file_manager import CachingFileManager
from xarray.backends.locks import SerializableLock

from .exceptions import VideoReadError

VIDEO_LOCK = SerializableLock()

compressor = numcodecs.registry.get_codec(dict(id="mp4"))


def _key_length(key, length):
    if isinstance(key, slice):
        return len(range(*key.indices(length)))
    elif is_scalar(key):
        return 1
    else:
        return length


class VideoArrayWrapper(BackendArray):
    """A wrapper around video dataset objects"""

    def __init__(self, manager, lock):
        self.manager = manager
        self.lock = lock

        reader = manager.acquire()

        codec = reader.streams[0].codec_context
        frames = reader.streams[0].frames
        width = codec.width
        height = codec.height

        self._shape = (frames, height, width, 3)
        self._dtype = np.dtype("uint8")

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self):
        return self._shape

    def _getitem(self, key):
        assert len(key) == 4, "video datasets should always be 4D"

        frame_key, y_key, x_key, band_key = key

        if isinstance(frame_key, slice):
            f0 = frame_key.start or 0
            f1 = frame_key.stop or self._shape[0]
            fstep = frame_key.step or 1
        elif is_scalar(frame_key):
            f0 = frame_key
            f1 = frame_key + 1
            fstep = 1
        else:
            f0 = 0
            f1 = self._shape[0]
            fstep = 1
        nf = (f1 - f0) // fstep
        ny = _key_length(y_key, self._shape[1])
        nx = _key_length(x_key, self._shape[2])
        nb = _key_length(band_key, self._shape[3])

        data = np.zeros((nf, ny, nx, nb), dtype="uint8")
        reader = self.manager.acquire()
        reader.seek(f0)
        ind0 = 0
        for i, frame in enumerate(reader.decode(video=0)):
            ind = frame.index
            if frame.index < f0:
                continue
            elif frame.index >= f1:
                break
            elif frame.index % fstep == 0:
                data[ind0] = frame.to_ndarray(format="rgb24")[y_key, x_key, band_key]
                ind0 += 1
        self.manager.close()
        data = np.squeeze(data)
        return data

    def __getitem__(self, key):
        return indexing.explicit_indexing_adapter(
            key, self.shape, indexing.IndexingSupport.BASIC, self._getitem
        )


def _open_video(filename, mode):
    return av.open(filename, mode=mode)


def _write_video(filename, array, fps=25, metadata={}):

    writer = av.open(filename, mode="w", format="mp4")

    nf, ny, nx, nb = array.shape

    stream = writer.add_stream("h264", rate=fps)
    stream.thread_type = "AUTO"

    stream.width = nx
    stream.height = ny
    stream.pix_fmt = "yuv420p"

    for frame_i in array:
        frame = av.VideoFrame.from_ndarray(frame_i, format="rgb24")
        for packet in stream.encode(frame):
            writer.mux(packet)

    # Flush stream
    for packet in stream.encode():
        writer.mux(packet)

    writer.close()


def open_video(filename, start_time=None, **kwargs):
    """Video file into an xarray dataset.

    This reads a video into an xarray dataset with the video in a DataArray.
    If a start time is provided, a time axis will be created for the frames.

    Args:
        filename (string): filename of videos to open
        start_time (:class:`numpy.datetime64`): Start time of video

    Returns:
        dataset (:class:`xarray.Dataset`): Dataset with video as a DataArray

    Raises:
        VideoReadError: Missing or incompatible files
    """

    manager = CachingFileManager(
        _open_video,
        filename,
        lock=VIDEO_LOCK,
        mode="r",
        kwargs=kwargs,
    )
    reader = manager.acquire()

    codec = reader.streams[0].codec_context
    frames = reader.streams[0].frames
    fps = int(reader.streams[0].rate)
    width = codec.width
    height = codec.height

    coords = {"channel": ["R", "G", "B"]}
    coords["pixel_x"] = np.arange(width)
    coords["pixel_y"] = np.arange(height)
    if start_time:
        times = np.datetime64(start_time) + np.arange(
            0, 1000 * frames / fps, 1000 / fps
        ).astype("<m8[ms]")
        coords["time"] = ("frame", times)
    else:
        coords["frame"] = np.arange(frames)

    # Attributes
    attrs = {"fps": fps, "_video": codec.name}
    data = indexing.LazilyIndexedArray(VideoArrayWrapper(manager, VIDEO_LOCK))

    dataset = Dataset(
        data_vars={
            "video": DataArray(
                data=data,
                dims=("frame", "pixel_y", "pixel_x", "channel"),
                coords=coords,
                attrs=attrs,
            )
        },
    )
    dataset["video"].encoding = {
        "chunks": [frames, height, width, 3],
        "compressor": compressor,
    }

    # Make the file closeable
    dataset.set_close(manager.close)

    return dataset
