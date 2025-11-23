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

    # ------------------------------------------------------------------
    # Handler lookup helpers
    # ------------------------------------------------------------------
    def handler_members(self, channel: str | None = None) -> dict:
        """Return immediate child handlers metadata (optionally filtered by channel)."""
        target_channel = channel if channel is not None else self.CHANNEL_CODE or None
        return self.publisher.api.members(channel=target_channel).get("children", {})

    def get_handler(self, name: str, channel: str | None = None):
        """Return handler instance by name if available (respecting channel filter)."""
        meta = self.handler_members(channel=channel).get(name)
        if not meta:
            return None
        return meta.get("instance")

    def list_handlers(self, channel: str | None = None) -> list:
        """Return list of published handler names."""
        return list(self.handler_members(channel=channel).keys())

    def get_handlers(self, channel: str | None = None) -> dict:
        """Return mapping name -> handler instance."""
        handlers = {}
        for name, meta in self.handler_members(channel=channel).items():
            instance = meta.get("instance")
            if instance is not None:
                handlers[name] = instance
        return handlers
