import xarray
import numpy
import av

from .exceptions import VideoDisplayError, VideoWriteError
from .backend import _write_video

_MAX_VIDEO_SIZE = 1024000000


@xarray.register_dataarray_accessor("video")
class VideoArray:
    """Video extension for :class:`xarray.DataArray`.

    Implements operations on a dataset which includes video data
    """

    def __init__(self, xarray_arr):
        self._arr = xarray_arr

    def _check_video(self, ndim=4):
        if len(self._arr.shape) != ndim or self._arr.shape[-1] != 3:
            raise VideoError(
                f"Expected array with {ndim} dimensions and with 3 channels in last dimension"
            )
        if self._arr.dtype != "uint8":
            raise VideoError("Expected uint8 dtype")
        return numpy.prod(self._arr.shape[:-1])

    def plot(self, **kwargs):
        """Plot DataArray frame as an image using matplotlib.imshow

        Raises:
            VideoError: if DataArray does not represent an image
        """
        try:
            import matplotlib.pyplot as plt
        except:
            raise VideoDisplayError("Need matplotlib installed to plot video")

        self._check_video(3)
        plt.imshow(self._arr.values, **kwargs)
        plt.show()

    def play(self, interval=10, repeat=False, **kwargs):
        """Play DataArray as a video using matplotlib.animation.

        All the video data is loaded into buffered in memory before rendering. Large video sequences cannot be played with this function.
        Note that this function is unlikely to play the video at the correct frame rate.

        Args:
            start_time (Union[datetime.datetime,str,:class:`numpy.datetime64`], "optional*): Start time of video array
            interval (int, *optional*): Interval in milliseconds between each frame render (default 0)
            repeat (bool, *optional*): Repeat animation (default False)

        Kwargs:
            kwargs are passed to matplotlib.pyplot.figure

        Raises:
            VideoError: if DataArray does not represent an video or the video array is too large
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.animation as animation

        except:
            raise VideoDisplayError("Need matplotlib installed to play video")

        nsize = self._check_video()
        if nsize > _MAX_VIDEO_SIZE:
            raise VideoDisplayError("Video too large to buffer")

        fps = self._arr.attrs.get("fps", 1)
        buffer = self._arr.values

        fig = plt.figure(**kwargs)
        ax = fig.gca()
        im = ax.imshow(buffer[0], animated=True)
        frame_coords = []
        for c in self._arr.coords:
            if "frame" in self._arr.coords[c].dims:
                frame_coords.append(self._arr.coords[c])

        def update_frame(i):
            frame = buffer[i]
            im.set_array(frame)
            ftime = i / fps
            ax.set_title(
                " ".join([c.name + ": " + str(c[i].values) for c in frame_coords])
            )
            return (im,)

        ani = animation.FuncAnimation(
            fig,
            update_frame,
            frames=range(len(self._arr)),
            interval=interval,
            repeat=repeat,
        )
        plt.show()

    def to_video(self, filename):
        """Write DataArray to a video file

        Args:
            filename (string): name of output file

        Raises:
            VideoWriteError: Incompatible DataArray or file write error

        """

        self._check_video()

        try:
            _write_video(
                filename, [self._arr.values], fps=self._arr.attrs.get("fps", 25)
            )
        except Exception as e:
            raise VideoWriteError(f"Error writing to file {filename}: {e}")
