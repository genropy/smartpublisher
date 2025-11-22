"""BaseChannel - common base class for Publisher channels."""

from smartroute.core import RoutedClass


class BaseChannel(RoutedClass):
    """Abstract base for channels (CLI/HTTP/etc.)."""

    CHANNEL_CODE: str = ""

    def __init__(self, registry):
        self.registry = registry

    @property
    def publisher(self):
        """Convenience accessor to the owning publisher via registry."""
        return self.registry.publisher

    def run(self, *args, **kwargs):
        """Start the channel. Must be implemented by subclasses."""
        raise NotImplementedError("Channel must implement run()")  # pragma: no cover

    def describe(self) -> dict:
        """Return basic channel metadata."""
        return {
            "class": self.__class__.__name__,
            "doc": (self.__class__.__doc__ or "").strip(),
            "channel_code": self.CHANNEL_CODE,
        }
