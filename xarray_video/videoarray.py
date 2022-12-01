import xarray
import matplotlib.pyplot as plt

from .exceptions import VideoError


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
        plt.imshow(self.values)
        plt.show()
