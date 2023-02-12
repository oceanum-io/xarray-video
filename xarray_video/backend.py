###Video backend for xarray based on the xarray rasterio backend


import os
import warnings
import tempfile

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
TEMPDIR = os.path.join(tempfile.gettempdir(), "xarray_video")
if not os.path.exists(TEMPDIR):
    os.mkdir(TEMPDIR)

compressor = numcodecs.registry.get_codec(dict(id="h264"))


def _key_length(key, length):
    if isinstance(key, slice):
        return len(range(*key.indices(length)))
    elif is_scalar(key):
        return 1
    else:
        return length


class VideoArrayWrapper(BackendArray):
    """A wrapper around video dataset objects"""

    def __init__(self, manager, lock, shape):
        self.manager = manager
        self.lock = lock

        reader = manager.acquire()
        stream = reader.streams.video[0]

        self._shape = shape
        self._dtype = np.dtype("uint8")

        ts0 = int((100 * av.time_base) / stream.average_rate) + stream.start_time
        reader.seek(ts0)
        for frame in reader.decode(stream):
            dt = frame.dts - stream.start_time
            self._can_seek = dt > 0
            break
        manager.close()

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self):
        return self._shape

    def _getitem(self, key):
        assert len(key) == 4, "video DataArrays should always be 4D"

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
        nf = len(range(f0, f1, fstep))
        ny = _key_length(y_key, self._shape[1])
        nx = _key_length(x_key, self._shape[2])
        nb = _key_length(band_key, self._shape[3])

        data = np.zeros((nf, ny, nx, nb), dtype="uint8")
        reader = self.manager.acquire()
        stream = reader.streams.video[0]
        if self._can_seek:
            ts0 = int((f0 * av.time_base) / stream.average_rate) + stream.start_time
            reader.seek(ts0)
            frame_start = -1
        else:
            frame_start = 0
        ind0 = 0
        for i, frame in enumerate(reader.decode(video=0)):
            if frame_start < 0:
                dts = frame.dts
                if (
                    dts is None
                ):  # Some packets at start have dts=None, same for fluxhing packets at end
                    if packet.buffer_size > 0:
                        dts = 0
                    else:
                        dts = 1e10
                frame_start = int(dts * stream.time_base * stream.rate)
            ind = frame_start + i
            if ind < f0:
                continue
            elif ind >= f1:
                break
            elif ind % fstep == 0:
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
    stream.pix_fmt = "yuvj420p"

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
    stream = reader.streams.video[0]
    codec = stream.codec_context
    frames = stream.frames
    # If the frame count is not in metadata, this is likely a matroska file. Then seeking will likely not work either
    # Solution is to scan the file using to demux to count the frames
    if frames == 0:
        for packet in reader.demux(stream):
            if packet.buffer_size > 0:
                frames += 1

    fps = int(stream.average_rate)
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
    data = indexing.LazilyIndexedArray(
        VideoArrayWrapper(
            manager,
            VIDEO_LOCK,
            (
                frames,
                height,
                width,
                3,
            ),
        )
    )

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
    if start_time:
        dataset = dataset.set_xindex("time")

    # Set the default zarr compressor and assign preferred chunk sizes
    dataset["video"].encoding = {
        "preferred_chunks": {"channel": 3, "pixel_y": height, "pixel_x": width},
    }

    # Make the file closeable
    dataset.set_close(manager.close)

    return dataset
