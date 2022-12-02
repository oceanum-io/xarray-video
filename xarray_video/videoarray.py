import xarray
import av
import matplotlib.pyplot as plt

from .exceptions import VideoError, VideoWriteError
from .backend import _write_video


@xarray.register_dataarray_accessor("video")
class VideoArray(xarray.DataArray):
    """Video extension for :class:`xarray.DataArray`.

    Implements operations on a dataset which includes video data
    """

    def plot(self):
        """Plot DataArray as an image using matplotlib.imshow

        Raises:
            VideoError: if DataArray does not represent an image
        """
        if len(self.shape) != 3 or self.shape[2] != 3:
            raise VideoError("Expected 3D array with 3 channels in last dimension")
        if self.dtype != "uint8":
            raise VideoError("Expected uint8 dtype")
        plt.imshow(self.values)
        plt.show()

    def to_video(self, filename):
        """Write DataArray to a video file

        Args:
            filename (string): name of output file

        Raises:
            VideoWriteError: Incompatible DataArray or file write error

        """

        if len(self.shape) != 4 or self.shape[3] != 3:
            raise VideoError("Expected 4D array with 3 channels in last dimension")
        if self.dtype != "uint8":
            raise VideoError("Expected uint8 dtype")

        try:
            _write_video(filename, [self.values], fps=self.attrs.get("fps", 25))
        except Exception as e:
            raise VideoWriteError(f"Error writing to file {filename}: {e}")
