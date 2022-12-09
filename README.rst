
Xarray extension for working with video data.

**This project is in an early stage of development. Please be patient with any bugs. Any contributuons are welcome.**


* MIT license
* Documentation: https://xarray-video.readthedocs.io.
* Github: https://github.com/oceanum-io/xarray-video


Features
--------

* Xarray backend to read video into an xarray dataset
* Xarray accessor for time and/or space stacked video DataArrays
* Zarr video codec for efficient compression of video in zarr chunks. Up to 100x improvement over blosc for video data.
* Xarray accessor for video Datasets for writing to zarr using the video codec
* Simple plotting and play previews to view video


Uses
----

* Attach coordinates (for example time or location) to the video frames dimension
* Load video into DaraArrays for easy subsetting
* Easily convert video and frames to other formats such as netcdf or geotiff
* Store video in an efficient chunked format within zarr
* Create massive lazy access video archives with zarr
* Store multiple videos (for example stereo camera) in the same archive with a consistent time and/or spatial reference.


Limitations
-----------

The library uses [PyAV](https://pyav.org) to read and write to/from video files. It will be limited to the same set of formats and codecs as your PyAV installation.

Although video file access and zarr archive access is lazy, once video data is loaded it is in uncompressed uint8 darrays. Trying to do dataset.load on large video files will exhaust your RAM very quickly.

The play preview is only intended as a diagnostic tool. It buffers the entire video as an array before display so cannot handle larger arrays. The play preview is also unlikely to play in realtime for larger videos.


Credits
-------

This package was developed by `Oceanum Numerical <https://www.oceanum.science>`_, with input from our development partners and contributors.
