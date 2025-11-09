"""
Publisher - Base class for publishing handlers with CLI/API exposure.
"""

from smartswitch import Switcher


class Publisher:
    """
    Base class for applications that publish handlers with SmartSwitch APIs.

    Provides:
    - Handler registration via publish()
    - Automatic parent_api injection
    - CLI and HTTP/OpenAPI exposure control
    - Multi-modal run() method

    Example:
        class MyApp(Publisher):
            def initialize(self):
                self.users = UserHandler()
                self.publish('users', self.users,
                           cli=True, openapi=True,
                           cli_name='users',
                           http_path='/api/v1/users')

        if __name__ == "__main__":
            app = MyApp()
            app.run()  # Auto-detect CLI or HTTP mode
    """

    def __init__(self):
        """
        Initialize Publisher.

        Creates parent_api Switcher and calls initialize() hook.
        """
        self.parent_api = Switcher(name="root")
        self.published_instances = {}
        self._cli_handlers = {}
        self._openapi_handlers = {}

        # Subclass MUST implement initialize()
        if not hasattr(self, 'initialize'):
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement initialize() method"
            )

        self.initialize()

    def publish(self, name: str, target_object, cli: bool = True, openapi: bool = True,
                cli_name: str | None = None, http_path: str | None = None):
        """
        Publish an object and register for CLI/OpenAPI exposure.

        Args:
            name: Name for the published instance
            target_object: Object to publish (must inherit from PublishedClass)
            cli: Expose via CLI (default: True)
            openapi: Expose via OpenAPI/HTTP (default: True)
            cli_name: Custom CLI name (default: same as name)
            http_path: Custom HTTP path (default: /{name})

        Raises:
            TypeError: If target_object is not publishable
        """
        # Inject parent_api (REQUIRED)
        try:
            target_object.parent_api = self.parent_api
        except AttributeError:
            raise TypeError(
                f"Cannot publish {type(target_object).__name__}: "
                f"class is not publishable. It must inherit from PublishedClass"
            ) from None

        # Save instance
        self.published_instances[name] = target_object

        # Register for exposure with custom names/paths
        if cli:
            effective_cli_name = cli_name if cli_name is not None else name
            self._cli_handlers[effective_cli_name] = target_object
        if openapi:
            effective_http_path = http_path if http_path is not None else f"/{name}"
            self._openapi_handlers[effective_http_path] = target_object

    def run(self, mode: str | None = None, port: int = 8000):
        """
        Run the application in specified mode.

        Args:
            mode: 'cli', 'http', or None (auto-detect from sys.argv)
            port: Port for HTTP mode (default: 8000)
        """
        if mode is None:
            # Auto-detect
            import sys
            if len(sys.argv) > 1:
                mode = 'cli'
            else:
                mode = 'http'

        if mode == 'cli':
            self._run_cli()
        elif mode == 'http':
            self._run_http(port)
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'cli' or 'http'")

    def _run_cli(self):
        """Run CLI mode (to be implemented)."""
        raise NotImplementedError("CLI mode not yet implemented")

    def _run_http(self, port: int):
        """Run HTTP mode (to be implemented)."""
        raise NotImplementedError("HTTP mode not yet implemented")
