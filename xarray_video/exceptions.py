class VideoError(Exception):
    pass


class VideoReadError(VideoError):
    pass


class VideoWriteError(VideoError):
    pass


class VideoProcessingError(VideoError):
    pass


class VideoDisplayError(VideoError):
    pass
