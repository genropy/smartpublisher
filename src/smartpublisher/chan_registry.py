"""
Channel Registry - Autodiscovery and management of channels.

Channels are transport layers (CLI, HTTP, WebSocket, etc.) that expose
the business logic of apps.

Channel metadata convention:
- Each channel module may expose CHANNEL_CODES mapping code -> description.
  The registry aggregates these to inform plugins about available types.
"""

from smartroute.core import Router, RoutedClass, route


class ChanRegistry(RoutedClass):
    """
    Registry for managing channels.

    Autodiscovers available channels and creates instances.
    """

    def __init__(self, publisher):
        """
        Initialize registry, autodiscover and create channels.

        Args:
            publisher: Publisher instance to pass to channels
        """
        super().__init__()
        # Router exposing registry commands
        self.api = Router(self, name="api").plug("pydantic")
        self.publisher = publisher
        self._channels = self._register_channels()
        self.channel_codes = self._collect_channel_codes()

    def _register_channels(self) -> dict:
        """
        Build the available channels map {name: instance}.
        """
        channels: dict[str, object] = {}

        # CLI channel
        try:
            from .channels.cli_channel import CLIChannel

            channels["cli"] = CLIChannel(self)
        except ImportError:
            pass

        # HTTP channel
        try:
            from .channels.http_channel import PublisherHTTP

            channels["http"] = PublisherHTTP(self)
        except ImportError:
            pass

        return channels

    def _collect_channel_codes(self) -> dict:
        """Aggregate CHANNEL_CODE from registered channel classes."""
        codes = {}
        for chan in self._channels.values():
            code = getattr(chan, "CHANNEL_CODE", "")
            if code:
                codes[str(code)] = getattr(chan.__class__, "__doc__", "") or ""
        return codes

    @route("api")
    def get_available_channels(self) -> dict:
        """
        Get list of available channel names.

        Returns:
            dict: Channel information
        """
        return {"total": len(self._channels), "channels": list(self._channels.keys())}

    @route("api")
    def describe(self, name: str) -> dict:
        """
        Describe a channel by name.
        """
        chan_name = (name or "").lower()
        if chan_name not in self._channels:
            return {
                "error": f"Channel '{chan_name}' not available",
                "available": list(self._channels.keys()),
            }
        chan = self._channels[chan_name]
        meta = {
            "name": chan_name,
            "class": chan.__class__.__name__,
            "doc": (chan.__class__.__doc__ or "").strip(),
        }
        codes = getattr(chan, "CHANNEL_CODES", None)
        if codes:
            meta["channel_codes"] = dict(codes)
        return meta

    @route("api")
    def list(self) -> dict:
        """Alias of get_available_channels for convenience."""
        return self.get_available_channels()

    @route("api")
    def run(self, name: str = "http", port: int | None = None, **options):
        """
        Run a channel by name (delegates to channel.run).
        """
        chan_name = (name or "").lower()
        try:
            chan = self.get(chan_name)
        except KeyError:
            return {
                "error": f"Channel '{chan_name}' not available",
                "available": list(self._channels.keys()),
            }
        run_opts = dict(options)
        if port is not None:
            run_opts.setdefault("port", port)
        result = chan.run(**run_opts)
        return {"status": "started", "channel": chan_name, "options": run_opts, "result": result}

    def get(self, name: str):
        """
        Get a channel instance by name.

        Args:
            name: Channel identifier ('cli', 'http', etc.)

        Returns:
            Channel instance

        Raises:
            KeyError: If channel not found
        """
        if name not in self._channels:
            raise KeyError(
                f"Channel '{name}' not available. Available: {self.get_available_channels()}"
            )

        return self._channels[name]

    @property
    def channels(self) -> dict:
        """
        Get all channel instances.

        Returns:
            dict: {channel_name: channel_instance}
        """
        return self._channels
