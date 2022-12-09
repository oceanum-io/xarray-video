from numcodecs.registry import get_codec, register_codec

from .codecs.h264 import H264

register_codec(H264)


from .videodataset import VideoDataset
from .videoarray import VideoArray
from .backend import open_video

"""Top-level package for xarray-video."""

__author__ = """Oceanum Developers"""
__email__ = "developers@oceanum.science"
__version__ = "0.2.3"
