import os
import tempfile
import numpy
import io

from numcodecs.abc import Codec
from numcodecs.compat import ndarray_copy, ensure_contiguous_ndarray

import av


class H264(Codec):
    """Codec providing compression using h264 via pyav

    Parameters
    ----------
    fps : int (optional)
        Frames per second in compressed chunk (default 25)
    crf : int (optional)
        Constant Rate Factor (default None). The range of the CRF
        scale is 0–51, where 0 is lossless, and 51 is worst quality
        possible. If None will use the ffmepg defautt (23).
    """

    codec_id = "h264"

    def __init__(self, fps=25, crf=None):
        self.fps = fps
        self.crf = crf

    def encode(self, buf):

        # normalise input
        nf, ny, nx, nb = buf.shape

        # write chunk as video file
        data = io.BytesIO()
        writer = av.open(data, mode="w", format="mp4")

        stream = writer.add_stream("h264", rate=self.fps)
        writer.streams.video[0].thread_type = "AUTO"

        stream.width = nx
        stream.height = ny
        stream.pix_fmt = "yuv420p"
        stream.options = {} if self.crf is None else {"crf": str(self.crf)}

        for frame_i in buf:
            frame = av.VideoFrame.from_ndarray(frame_i, format="rgb24")
            for packet in stream.encode(frame):
                writer.mux(packet)

        # Flush stream
        for packet in stream.encode():
            writer.mux(packet)

        writer.close()
        data.seek(0)
        return data.read()

    def decode(self, buf, out=None):
        # normalise inputs
        buf = ensure_contiguous_ndarray(buf)

        stream = io.BytesIO(buf)
        reader = av.open(stream)
        reader.streams.video[0].thread_type = "AUTO"

        codec = reader.streams[0].codec_context
        frames = reader.streams[0].frames
        width = codec.width
        height = codec.height

        if out is not None:
            out = ensure_contiguous_ndarray(out)

        data = numpy.zeros((frames, height, width, 3), dtype="uint8")
        for i, frame in enumerate(reader.decode(video=0)):
            data[i] = frame.to_ndarray(format="rgb24")

        reader.close()
        return ndarray_copy(data, out)
