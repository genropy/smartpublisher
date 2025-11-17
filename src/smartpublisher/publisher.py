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
    from .registry import AppRegistry, get_local_registry, get_global_registry
    from .channels.cli import PublisherCLI
    from .channels.http import PublisherHTTP
except ImportError:
    from registry import AppRegistry, get_local_registry, get_global_registry
    from channels.cli import PublisherCLI
    from channels.http import PublisherHTTP


class Publisher:
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
        # Initialize registry
        if registry_path:
            self.registry = AppRegistry(registry_path)
        elif use_global:
            self.registry = get_global_registry()
        else:
            self.registry = get_local_registry()

        # Initialize channels
        self.channels = {
            'cli': PublisherCLI(self),
            'http': PublisherHTTP(self)
        }

        # Publisher's own Router (for system-level commands)
        # Note: For now, keep as simple attribute. Can be converted to RoutedClass pattern later.
        self.api = None  # TODO: Implement if needed for system commands

        # Currently loaded apps
        self.loaded_apps = {}

    def load_app(self, app_name: str):
        """
        Load an app from registry.

        Args:
            app_name: Name of the app to load

        Returns:
            PublishedClass instance
        """
        # Check if already loaded
        if app_name in self.loaded_apps:
            return self.loaded_apps[app_name]

        # Load from registry
        app = self.registry.load(app_name)

        # Set publisher reference
        if hasattr(app, '_set_publisher'):
            app._set_publisher(self)

        # Call on_add lifecycle hook
        if hasattr(app, 'smpub_on_add'):
            app.smpub_on_add()
            # TODO: Handle result (logging, etc.)

        # Cache loaded app
        self.loaded_apps[app_name] = app

        return app

    def unload_app(self, app_name: str):
        """
        Unload an app.

        Args:
            app_name: Name of the app to unload

        Returns:
            dict: Unload result
        """
        if app_name not in self.loaded_apps:
            return {
                "error": f"App '{app_name}' not loaded"
            }

        app = self.loaded_apps[app_name]

        # Call on_remove lifecycle hook
        if hasattr(app, 'smpub_on_remove'):
            app.smpub_on_remove()
            # TODO: Handle result

        # Remove from cache
        del self.loaded_apps[app_name]

        return {
            "status": "unloaded",
            "app": app_name
        }

    def get_channel(self, channel_name: str):
        """
        Get a channel by name.

        Args:
            channel_name: 'cli', 'http', etc.

        Returns:
            Channel instance

        Raises:
            KeyError: If channel not found
        """
        return self.channels[channel_name]

    def add_channel(self, channel_name: str, channel_instance):
        """
        Add a custom channel.

        Args:
            channel_name: Channel identifier
            channel_instance: Channel object
        """
        self.channels[channel_name] = channel_instance

    def run_cli(self, args: list = None):
        """
        Run CLI channel.

        Args:
            args: CLI arguments (uses sys.argv if None)
        """
        cli = self.get_channel('cli')
        cli.run(args)

    def run_http(self, port: int = 8000, **kwargs):
        """
        Run HTTP server.

        Args:
            port: Port to listen on
            **kwargs: Additional uvicorn options
        """
        http = self.get_channel('http')
        http.run(port=port, **kwargs)


# Singleton instance for convenience
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
