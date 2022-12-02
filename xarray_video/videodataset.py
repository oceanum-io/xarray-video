import xarray
import warnings

from .exceptions import VideoWriteError
from .backend import compressor, _write_video


@xarray.register_dataset_accessor("video")
class VideoDataset(xarray.Dataset):
    """Video extension for :class:`xarray.Dataset`.

    Implements operations on a dataset which includes video data
    """

    def to_zarr(self, *args, **kwargs):
        (
            """Write to zarr using a video codec for comaptible data variables.
        """
            + xarray.core.dataset.Dataset.to_zarr.__doc__
        )
        for v in self.data_vars:
            if len(self.shape) == 4 and self.shape[3] == 3:
                self[v].encoding = {
                    **self[v].encoding,
                    "compressor": compressor,
                    "chunks": self[v].shape,
                }
        super().to_zarr(
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
            for v in self.data_vars:
                if data_var and v != data_var:
                    continue
                video_array = self.data_vars[v]
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
