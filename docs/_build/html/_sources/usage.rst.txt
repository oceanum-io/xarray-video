=====
Usage
=====

Import the library::

    import xarray_video as xv

This will also automatically import and register the video accessors and the zarr codecs for video data

Open a video file
-----------------

If you don't have file to test, grab one of the xarray-video test files::

    import urllib.request
    urllib.request.urlretrieve("https://github.com/oceanum-io/xarray-video/raw/main/tests/data/ocean_test.mp4", "ocean_test.mp4")

    v=xv.open_video("ocean_test.mp4")
    print(v)

Create a time coordinate by defining the start time of the video::

     v=xv.open_video("ocean_test.mp4", start_time="2022-01-01 00:00:00")
     print(v)

Have look at the last frame of the video::

    v["video"][-1].video.plot()


Play a preview::

    v["video"].video.play()

If you have problems with the matplotlib graphics backend, try using ipython. 
In a notebook environment, you may have to do %matplotlib widget to get the play function to work correctly.



Subset a video dataset
----------------------

Subset the first 100 frames of the video::

    v_subset=v.isel(frame=slice(0,100))

get only once every 25 frames::

    v_subset=v.isel(frame=slice(None,None,25))

or if you want to subset by a time coordinate::

    v_subset=v.sel(time=slice("2022-01-01 00:00:00", "2022-01-01 00:00:10"))

Get a part of the video frame::

    v_subset=v.isel(pixel_x=slice(0,500))
    v_subset["video"].video.play()



Write back to a file
--------------------

Write to video file::

    v_subset.video.to_video("onlyhalf.mp4")

Write to netcdf::

    v_subset.to_netcdf("my_video.nc")

Write to zarr using the video codec (note the *video* accessor)::

    v_subset.video.to_zarr("video_codec.zarr")
    !du -h video_codec.zarr

Or use vanilla zarr, if you want::

    v_subset.to_zarr("video_blosc.zarr")
    !du -h video_blosc.zarr

Open the zarr archive with video codec to check xarray can open it::

    import xarray as xr
    vz=xr.open_dataset("video_h264.zarr")
    vz["video"].video.play()


Test compression performance
----------------------------

Write the complete dataset to zarr using vanilla blosc and the video codec::

    t0=time.time()
    v.to_zarr("test_blosc.zarr", mode="w")
    t1=time.time()
    t_blosc=t1-t0

    t0=time.time()
    v.video.to_zarr("test_h264.zarr", mode="w")
    t1=time.time()
    t_h264=t1-t0


Get sizes of the zarr archives::

    from pathlib import Path

    h264_directory = Path('video_h264.zarr')
    h264_size=sum(f.stat().st_size for f in h264_directory.glob('**/*') if f.is_file())
    blosc_directory = Path('video_blosc.zarr')
    blosc_size=sum(f.stat().st_size for f in blosc_directory.glob('**/*') if f.is_file())

    compression_ratio=(blosc_size/h264_size) 

    time_ratio=(t_blosc/t_h264)

We can see that for video data the video codec compression is more than 300x better than blosc. But it is also about a factor of 2 slower.


Just for fun ;), calculate the `Weissman score <https://en.wikipedia.org/wiki/Weissman_score>`_ for the complete video::

    import numpy as np

    weissman=compression_ratio*np.log(t_blosc)/np.log(t_264)

Weissman score of almost 250!!! Richard Hendricks would be pretty happy with that. 







