class NyaaDownloaderError(Exception):
    """Base class for errors shown to the user."""


class NetworkError(NyaaDownloaderError):
    """The remote service could not be reached or answered with an error."""


class UnknownUploaderError(NyaaDownloaderError):
    """Nyaa has no user with this name."""

    def __init__(self, uploader: str) -> None:
        super().__init__(f"Nyaa has no uploader named “{uploader}”.")
        self.uploader = uploader


class Cancelled(NyaaDownloaderError):
    """The operation was cancelled by the user."""
