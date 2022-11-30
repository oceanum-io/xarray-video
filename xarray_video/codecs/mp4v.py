import os
import tempfile
import numpy

from numcodecs.abc import Codec
from numcodecs.compat import ndarray_copy, ensure_contiguous_ndarray

import cv2


class mp4v(Codec):
    """Codec providing compression using mp4v via OpenCV.
    Parameters
    ----------
    fps : int (optional)
        Frames per second in compressed chunk (default 25)
    """

    codec_id = "mp4v"

    def __init__(self, fps=25):
        self.fps = fps

    def encode(self, buf):

        # normalise input
        nf, ny, nx, nb = buf.shape

        # create temporary file
        tmp = tempfile.NamedTemporaryFile("wb", delete=False)

        # write chunk as video file
        writer = cv2.VideoWriter(tmp.name + ".mp4", 0x7634706D, self.fps, (nx, ny))
        for frame in buf:
            writer.write(frame)
        writer.release()

        # read and spool file as buffer
        with open(tmp.name + ".mp4", "rb") as f:
            compressed = f.read()
        os.unlink(tmp.name)
        return compressed

    def decode(self, buf, out=None):
        # normalise inputs
        buf = ensure_contiguous_ndarray(buf)

        # create temporary file
        tmp = tempfile.NamedTemporaryFile("wb", delete=False)
        with open(tmp.name, "wb") as f:
            f.write(buf)
            f.close()

        video = cv2.VideoCapture(tmp.name)
        frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if out is not None:
            out = ensure_contiguous_ndarray(out)

        data = numpy.zeros((frames, height, width, 3), dtype="uint8")
        i = 0
        while True:
            ok, image = video.read()
            if not ok:
                break
            data[i] = image
            i += 1
        video.release()
        os.unlink(tmp.name)
        return ndarray_copy(data, out)
