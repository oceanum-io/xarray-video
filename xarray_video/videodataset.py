import xarray
from .backend import compressor


@xarray.register_dataset_accessor("video")
class VideoDataset(xarray.Dataset):
    """Video extension for :class:`xarray.Dataset`.

    Implements operations on a dataset which includes video data
    """

    def to_zarr(self, *args, **kwargs):
        (
            """Write to zarr using a video codec for comaptible data variables.
        """
            + xarray.core.dataset.Dataset.to_zarr.__doc__
        )
        for v in self.data_vars:
            if len(self.shape) == 4 and self.shape[3] == 3:
                self[v].encoding = {
                    **self[v].encoding,
                    "compressor": compressor,
                    "chunks": self[v].shape,
                }
        super().to_zarr(
            *args,
            **kwargs,
        )
