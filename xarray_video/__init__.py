from numcodecs.registry import get_codec, register_codec

from .codecs.mp4v import mp4v

register_codec(mp4v)


from .videodataset import VideoDataset
from .videoarray import VideoArray
from .backend import open_video

"""Top-level package for xarray-video."""

__author__ = """Oceanum Developers"""
__email__ = "developers@oceanum.science"
__version__ = "0.0.1"
