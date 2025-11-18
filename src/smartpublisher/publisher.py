"""
Publisher - Central coordinator for SmartPublisher system.

This is the ONE instance that manages:
- App registry (AppRegistry)
- Channels (CLI, HTTP, etc.)
- Published apps coordination

User apps inherit from PublishedClass, not Publisher.
"""

from pathlib import Path

# Try relative imports first (when used as package)
# Fall back to absolute imports (when run directly)
try:
    from smartroute import Router, route
    from .published import PublishedClass
    from .app_registry import AppRegistry
    from .chan_registry import ChanRegistry
except ImportError:
    from smartroute import Router, route
    from published import PublishedClass
    from app_registry import AppRegistry
    from chan_registry import ChanRegistry


class Publisher(PublishedClass):
    """
    Central Publisher coordinator.

    This is a singleton-like class that manages the entire system:
    - Registry of apps
    - Multiple channels (CLI, HTTP, etc.)
    - Coordination between apps and channels

    There is ONE Publisher per process.
    Apps inherit from PublishedClass, not Publisher.
    """

    def __init__(self, registry_path: Path = None, use_global: bool = False):
        """
        Initialize Publisher.

        Args:
            registry_path: Custom registry path (optional)
            use_global: Use global registry instead of local
        """
        super().__init__()

        # Core registry
        self.app_registry = AppRegistry(self, registry_path=registry_path, use_global=use_global)

        # Channel registry / instances
        self.chan_registry = ChanRegistry(self)

        # Publish registry handlers for CLI exposure
        self.publish("apps", self.app_registry)
        self.publish("chan", self.chan_registry)

    @route("api")
    def serve(self, channel: str = "http", **options):
        """
        Placeholder serve command exposed via API.

        Args:
            channel: Channel identifier to activate
            **options: Additional channel-specific options
        """
        return {
            "status": "disabled",
            "message": "Serve command not wired yet",
            "channel": channel,
            "options": options,
        }

    @route("api")
    def quit(self):
        """Placeholder quit command exposed via API."""
        return {
            "status": "disabled",
            "message": "Quit command not wired yet",
        }

    @route("api")
    def load_app(self, app_name: str):
        """
        Load an app via registry and publish it.

        Args:
            app_name: Name registered in AppRegistry
        """
        if app_name in self.app_registry.applications:
            return self.app_registry.applications[app_name]

        app = self.app_registry.load(app_name)

        if hasattr(app, '_set_publisher'):
            app._set_publisher(self)

        already_added = False
        try:
            already_added = object.__getattribute__(app, '_smpub_on_add_called')
        except AttributeError:
            already_added = False

        if hasattr(app, 'smpub_on_add') and not already_added:
            app.smpub_on_add()
            setattr(app, '_smpub_on_add_called', True)

        self.app_registry.applications[app_name] = app
        self.publish(app_name, app)

        return app

    @route("api")
    def unload_app(self, app_name: str):
        """
        Unload an application.

        Args:
            app_name: Registered application name
        """
        if app_name not in self.app_registry.applications:
            return {"error": f"App '{app_name}' not loaded"}

        app = self.app_registry.applications[app_name]

        already_removed = False
        try:
            already_removed = object.__getattribute__(app, '_smpub_on_remove_called')
        except AttributeError:
            already_removed = False

        if hasattr(app, 'smpub_on_remove') and not already_removed:
            app.smpub_on_remove()
            setattr(app, '_smpub_on_remove_called', True)

        # Remove from local registry bookkeeping
        del self.app_registry.applications[app_name]

        # Keep registry cache in sync (ignore errors if not tracked)
        try:
            self.app_registry.unload(app_name)
        except Exception:
            pass

        return {"status": "unloaded", "app": app_name}

    def get_channel(self, channel_name: str):
        """Return channel instance by name."""
        return self.chan_registry.get(channel_name)

    def add_channel(self, channel_name: str, channel_instance):
        """Register or override a channel instance."""
        self.chan_registry.channels[channel_name] = channel_instance

    def run_cli(self, args: list | None = None):
        """CLI entry point - delegates to CLI channel."""
        cli_channel = self.get_channel('cli')
        cli_channel.run(args)

    def run_http(self, port: int = 8000, **kwargs):
        """Run HTTP channel."""
        http_channel = self.get_channel('http')
        http_channel.run(port=port, **kwargs)


# # Singleton instance for convenience
_default_publisher = None


def get_publisher(use_global: bool = False) -> Publisher:
    """
    Get the default Publisher instance.

    Args:
        use_global: Use global registry

    Returns:
        Publisher instance
    """
    global _default_publisher

    if _default_publisher is None:
        _default_publisher = Publisher(use_global=use_global)

    return _default_publisher


# Module-level entry point for CLI
def main():
    """Entry point for smpub command."""
    publisher = Publisher()
    publisher.run_cli()


if __name__ == "__main__":
    main()
