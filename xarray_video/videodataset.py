import xarray
import warnings

from .exceptions import VideoWriteError
from .backend import compressor, _write_video

_DEFAULT_CHUNK_SIZE = 512000000


@xarray.register_dataset_accessor("video")
class VideoDataset:
    """Video extension for :class:`xarray.Dataset`.

    Implements operations on a dataset which includes video data
    """

    def __init__(self, xarray_dset):
        self._dset = xarray_dset

    def to_zarr(self, *args, chunk_sizes={}, **kwargs):
        (
            """Write to zarr using a video codec for compatible data variables. For non compatible variables, zarr defaults (or variable encoding) will be used.

        Kwargs:
            chunk_sizes (dict, *optional*): preferred chunk_sizes for frame, pixel_y and pixel_x dimensions

        """
            + xarray.core.dataset.Dataset.to_zarr.__doc__
        )
        encoding = {}
        for v in self._dset.data_vars:
            dv = self._dset.data_vars[v]
            if len(dv.shape) == 4 and dv.shape[3] == 3 and "_video" in dv.attrs:
                nf, ny, nx, nb = dv.shape
                ny0 = chunk_sizes.get("pixel_y", ny)
                nx0 = chunk_sizes.get("pixel_x", nx)
                nf0 = chunk_sizes.get("frame", _DEFAULT_CHUNK_SIZE // ny0 // nx0 // 3)
                encoding[v] = {
                    "compressor": compressor,
                    "chunks": [nf0, ny0, nx0, 3],
                }
        if "mode" in kwargs and kwargs["mode"] == "w":
            kwargs["encoding"] = {**kwargs.get("encoding", {}), **encoding}
        self._dset.to_zarr(
            *args,
            **kwargs,
        )

    def to_video(self, filename, data_var=None):
        """Write Dataset to a video file.

        Args:
            filename (string): name of output file
            data_var (string, Optional): Data variable to write as video streams.

        Raises:
            VideoWriteError: Incompatible DataArray or file write error

        """
        try:
            output_stream = None
            for v in self._dset.data_vars:
                if data_var and v != data_var:
                    continue
                video_array = self._dset.data_vars[v]
                if (
                    len(video_array.shape) == 4
                    and video_array.shape[3] == 3
                    and video_array.dtype == "uint8"
                ):
                    output_stream = video_array.values
            if output_stream is None:
                warnings.warn("No compatible DataArrays found")
            else:
                _write_video(
                    filename,
                    output_stream,
                    fps=video_array.attrs.get("fps", 25),
                )

        except Exception as e:
            raise VideoWriteError(f"Error writing to file {filename}: {e}")
