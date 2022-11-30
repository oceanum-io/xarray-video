import xarray


@xarray.register_dataset_accessor("video")
class VideoDataset(xarray.Dataset):
    """Video extension for :class:`xarray.Dataset`.
    Implements operations on a dataset which includes video data
    """
