###Video backend for xarray based on the xarray rasterio backend


import os
import warnings

import numpy as np
import cv2

from xarray import DataArray, Dataset
from xarray.core import indexing
from xarray.core.utils import is_scalar
from xarray.backends.common import BackendArray
from xarray.backends.file_manager import CachingFileManager
from xarray.backends.locks import SerializableLock

from .exceptions import VideoReadError

_extensions = [".avi"]

VIDEO_LOCK = SerializableLock()

_ERROR_MSG = (
    "The kind of indexing operation you are trying to do is not "
    "valid on video files. Try to load your data with ds.load()"
    "first."
)


class VideoArrayWrapper(BackendArray):
    """A wrapper around video dataset objects"""

    def __init__(self, manager, lock, vrt_params=None):
        self.manager = manager
        self.lock = lock

        video = manager.acquire()

        frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.fps = int(video.get(cv2.CAP_PROP_FPS))
        self.rgb_convert = video.get(cv2.CAP_PROP_CONVERT_RGB)
        self._shape = (frames, height, width, 3)
        self._dtype = np.dtype("uint8")

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self) -> tuple[int, ...]:
        return self._shape

    def _getitem(self, key):
        assert len(key) == 4, "video datasets should always be 4D"

        frame_key, y_key, x_key, band_key = key

        squeeze_axis = []
        if isinstance(frame_key, slice):
            f0 = frame_key.start or 0
            f1 = frame_key.stop or self._shape[0]
            fstep = frame_key.step or 1
        elif is_scalar(frame_key):
            f0 = frame_key
            f1 = frame_key + 1
            fstep = 1
            squeeze_axis = [0]
        else:
            f0 = 0
            f1 = self._shape[0]
            fstep = 1
        nf = (f1 - f0) // fstep

        i = f0
        ind = 0
        data = np.zeros((nf, ny, nx, nb), dtype="uint8")
        with self.lock:
            while i < f1:
                video = self.manager.acquire()
                video.set(cv2.CAP_PROP_POS_FRAMES, i)
                success, image = video.read()
                if not success:
                    break
                RGBimage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                data[ind, :, :, :] = RGBimage[y_key, x_key, band_key]
                i += fstep
                ind += 1

        if squeeze_axis:
            data = np.squeeze(data, axis=squeeze_axis)
        return data

    def __getitem__(self, key):
        return indexing.explicit_indexing_adapter(
            key, self.shape, indexing.IndexingSupport.OUTER, self._getitem
        )


def _open_video(filename, mode):
    return cv2.VideoCapture(filename)


def open_video(filename, start_time=None, **kwargs):
    """Video file into an xarray dataset.

    This reads a video into an xarray dataset with the video in a DataArray.
    If a start time is provided, a time axis will be created for the frames.

    Args:
        filename (string): filename of videos to open
        start_time (numpy.datetime64): Start time of video

    Returns:
        dataset (:class:`xarray.Dataset`): Dataset with video as a DataArray

    Raises:
        VideoReadError: Missing or incompatible files
    """

    lock = VIDEO_LOCK
    manager = CachingFileManager(
        _open_video,
        filename,
        lock=lock,
        mode="r",
        kwargs=kwargs,
    )
    video = manager.acquire()

    fps = int(video.get(cv2.CAP_PROP_FPS))
    frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    coords = {"band": ["R", "G", "B"]}
    coords["pixel_x"] = np.arange(width)
    coords["pixel_y"] = np.arange(height)
    if start_time:
        times = np.datetime64(time_start) + np.arange(
            0, 1000 * frames / fps, 1000 / fps
        ).astype("<m8[ms]")
        coords["time"] = ("frame", times)
    else:
        coords["frame"] = np.arange(frames)

    # Attributes
    attrs = {"fps": fps}
    data = indexing.LazilyIndexedArray(VideoArrayWrapper(manager, lock))

    dataset = Dataset(
        data_vars={
            "video": DataArray(
                data=data,
                dims=("frame", "pixel_y", "pixel_x", "band"),
                coords=coords,
                attrs=attrs,
            )
        }
    )

    # Make the file closeable
    # dataset.set_close(manager.release)

    return dataset
