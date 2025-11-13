"""
Publisher - Base class for publishing handlers with CLI/API exposure.
"""

import os
import sys
from pydantic import ValidationError
from smartswitch import Switcher
from smartasync import SmartasyncPlugin
from .published import PublisherContext
from .validation import validate_args, format_validation_error
from .interactive import prompt_for_parameters


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
            def on_init(self):
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

        Creates parent_api Switcher with plugin chain:
        1. LoggingPlugin (silent mode) - tracks all calls
        2. PydanticPlugin - validates and creates models
        3. SmartasyncPlugin - handles sync/async (must be last)

        Then calls on_init() hook if defined by subclass.
        """
        # Create root Switcher with plugins pre-configured in correct order
        self.parent_api = (
            Switcher(name="root")
            .plug("logging", mode="silent")  # First: track all calls (silent mode)
            .plug("pydantic")  # Second: validation and model generation
            .plug(SmartasyncPlugin())  # Last: async wrapping (must be final)
        )
        self.published_instances = {}
        self._cli_handlers = {}
        self._openapi_handlers = {}

        # Call on_init() hook if defined by subclass
        if hasattr(self, "on_init") and callable(self.on_init):
            self.on_init()
        else:
            # No on_init() defined - publish default help handler
            self._publish_default_help()

    def _publish_default_help(self):
        """Publish a default help handler when no on_init() is defined."""

        class DefaultHelp:
            """Default help handler - shown when Publisher has no on_init()."""

            def usage(self) -> dict:
                """Show how to implement a Publisher subclass."""
                return {
                    "message": "This Publisher has no handlers published yet",
                    "instructions": [
                        "1. Override on_init() in your Publisher subclass",
                        "2. Use self.publish(name, handler_instance) to publish handlers",
                        "3. Example: self.publish('myhandler', MyHandler())",
                    ],
                    "example": """
class MyPublisher(Publisher):
    def on_init(self):
        handler = MyHandler()
        self.publish('myhandler', handler)
""",
                }

        self.publish("help", DefaultHelp())

    def publish(
        self,
        name: str,
        target_object,
        cli: bool = True,
        openapi: bool = True,
        cli_name: str | None = None,
        http_path: str | None = None,
        switcher_name: str = "api",
    ):
        """
        Publish an object and register for CLI/OpenAPI exposure.

        Args:
            name: Name for the published instance
            target_object: Object to publish
            cli: Expose via CLI (default: True)
            openapi: Expose via OpenAPI/HTTP (default: True)
            cli_name: Custom CLI name (default: same as name)
            http_path: Custom HTTP path (default: /{name})
            switcher_name: Name of the Switcher class attribute (default: 'api')

        Raises:
            TypeError: If target_object uses __slots__ but doesn't include 'smpublisher' slot
        """
        # Create and inject PublisherContext
        context = PublisherContext(target_object, switcher_name=switcher_name)
        context.parent_api = self.parent_api

        try:
            target_object.smpublisher = context
        except AttributeError:
            # Handler uses __slots__ but doesn't include 'smpublisher'
            raise TypeError(
                f"Cannot publish {type(target_object).__name__}: "
                f"class uses __slots__ but doesn't include 'smpublisher' slot.\n"
                f"Add 'smpublisher' to your __slots__:\n\n"
                f"    class {type(target_object).__name__}:\n"
                f"        __slots__ = ('your_attrs', 'smpublisher')  # Add this!\n"
                f"        api = Switcher()\n"
            ) from None

        # Link handler's API to parent_api for hierarchical structure
        if hasattr(target_object.__class__, switcher_name):
            handler_api = getattr(target_object.__class__, switcher_name)
            # Set parent to establish parent-child relationship
            # This automatically registers the child via SmartSwitch's parent.setter
            handler_api.parent = self.parent_api

            # Apply plugins retroactively to ensure all handlers have required plugins
            self._ensure_plugins(handler_api)

        # Save instance
        self.published_instances[name] = target_object

        # Register for exposure with custom names/paths
        if cli:
            effective_cli_name = cli_name if cli_name is not None else name
            self._cli_handlers[effective_cli_name] = {
                "handler": target_object,
                "switcher_name": switcher_name,
            }
        if openapi:
            effective_http_path = http_path if http_path is not None else f"/{name}"
            self._openapi_handlers[effective_http_path] = {
                "handler": target_object,
                "name": name,
                "switcher_name": switcher_name,
            }

    def _ensure_plugins(self, handler_api):
        """
        Ensure handler has required plugins, applying them retroactively if needed.

        Required plugins for smpub:
        1. LoggingPlugin - for call tracking
        2. PydanticPlugin - for validation and model generation
        3. SmartasyncPlugin - for async wrapping (must be last)

        Args:
            handler_api: The Switcher instance from the handler class
        """
        # Get current plugin names
        current_plugins = {p.plugin_name for p in handler_api._plugins if hasattr(p, "plugin_name")}

        # Check for SmartasyncPlugin and remove it temporarily (must be last)
        smartasync_plugin = None
        for plugin in handler_api._plugins[:]:  # Copy list to modify during iteration
            if isinstance(plugin, SmartasyncPlugin):
                smartasync_plugin = plugin
                handler_api._plugins.remove(plugin)
                # Also remove from registry
                if "smartasync" in handler_api._plugin_registry:
                    del handler_api._plugin_registry["smartasync"]
                break

        # Track which plugins we add (for retroactive on_decorate)
        new_plugins = []

        # Add Logging if missing
        if "logger" not in current_plugins:
            handler_api.plug("logging", mode="silent")
            new_plugins.append(("logger", handler_api._plugins[-1]))

        # Add Pydantic if missing
        if "pydantic" not in current_plugins:
            handler_api.plug("pydantic")
            new_plugins.append(("pydantic", handler_api._plugins[-1]))

        # Re-add or add SmartasyncPlugin at the end
        if smartasync_plugin:
            handler_api._plugins.append(smartasync_plugin)
            handler_api._plugin_registry["smartasync"] = smartasync_plugin
        else:
            handler_api.plug(SmartasyncPlugin())

        # Apply on_decorate retroactively for newly added plugins
        if new_plugins:
            for method_name, method_func in handler_api._handlers.items():
                for plugin_name, plugin in new_plugins:
                    if hasattr(plugin, "on_decorate"):
                        plugin.on_decorate(method_func, handler_api)

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
                mode = "cli"
            else:
                mode = "http"

        if mode == "cli":
            self._run_cli()
        elif mode == "http":
            self._run_http(port)
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'cli' or 'http'")

    def _run_cli(self):
        """Run CLI mode."""
        args = sys.argv[1:]

        # General help
        if not args or args[0] in ["--help", "-h", "help"]:
            self._print_cli_help()
            return

        # Parse: handler_name [method_name] [method_args...]
        handler_name = args[0]

        # Check if handler exists
        if handler_name not in self._cli_handlers:
            print(f"Error: Unknown handler '{handler_name}'")
            print(f"\nAvailable handlers: {', '.join(self._cli_handlers.keys())}")
            print("Use --help to see full usage")
            sys.exit(1)

        # Handler help
        if len(args) == 1 or args[1] in ["--help", "-h", "help"]:
            self._print_handler_help(handler_name)
            return

        method_name = args[1]

        # Check for --interactive flag
        interactive = "--interactive" in args[2:] or "-i" in args[2:]
        if interactive:
            # Remove flag from args
            method_args = [a for a in args[2:] if a not in ["--interactive", "-i"]]
        else:
            method_args = args[2:]

        # Get handler instance and switcher name
        handler_info = self._cli_handlers[handler_name]
        handler = handler_info["handler"]
        switcher_name = handler_info["switcher_name"]

        # Get handler's Switcher
        if not hasattr(handler.__class__, switcher_name):
            print(
                f"Error: Handler '{handler_name}' has no Switcher (missing '{switcher_name}' class variable)"
            )
            sys.exit(1)

        switcher = getattr(handler.__class__, switcher_name)

        # Build full method name with prefix if needed
        prefix = getattr(switcher, "prefix", None) or ""
        full_method_name = f"{prefix}{method_name}"

        # Check if method exists on handler
        if not hasattr(handler, full_method_name):
            print(f"Error: Method '{method_name}' not found")
            print(f"Use 'smpub {sys.argv[0]} {handler_name} --help' to see available methods")
            sys.exit(1)

        # Get method
        method = getattr(handler, full_method_name)

        # Interactive mode: prompt for parameters
        if interactive:
            method_args = prompt_for_parameters(method)

        # Validate and convert arguments using Pydantic
        try:
            validated_params = validate_args(method, method_args)
        except ValidationError as e:
            print("Error: Invalid arguments")
            print(format_validation_error(e))
            print(f"\nUse 'smpub {sys.argv[0]} {handler_name} --help' to see method signature")
            sys.exit(1)

        # Call method with validated parameters
        try:
            result = method(**validated_params)
            if result is not None:
                print(result)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def _print_cli_help(self):
        """Print general CLI help."""
        app_name = self.__class__.__name__
        prog_name = os.path.basename(sys.argv[0])
        print(f"\n{app_name} - Publisher Application\n")
        print("Usage:")
        print(f"  {prog_name} <handler> <method> [args...]")
        print(f"  {prog_name} <handler> <method> --interactive\n")
        print("Options:")
        print("  --interactive, -i  Prompt for parameters interactively (requires textual)\n")
        print("Available handlers:")
        for name in sorted(self._cli_handlers.keys()):
            handler = self._cli_handlers[name]["handler"]
            doc = handler.__class__.__doc__ or "No description"
            doc = doc.strip().split("\n")[0]  # First line only
            print(f"  {name:15} {doc}")
        print(f"\nUse '{prog_name} <handler> --help' for handler-specific help")

    def _print_handler_help(self, handler_name):
        """Print help for a specific handler."""
        handler = self._cli_handlers[handler_name]["handler"]
        handler_class = handler.__class__
        prog_name = os.path.basename(sys.argv[0])

        print(f"\nHandler: {handler_name}")
        if handler_class.__doc__:
            print(f"Description: {handler_class.__doc__.strip()}\n")

        # Get API schema from handler
        if not hasattr(handler, "smpublisher"):
            print("No API methods available (handler not properly published)")
            return

        schema = handler.smpublisher.get_api_json()

        if not schema["methods"]:
            print("No API methods available")
            return

        print("Available methods:")

        for method_name in sorted(schema["methods"].keys()):
            method_info = schema["methods"][method_name]

            # Build parameter string
            params = []
            for param in method_info["parameters"]:
                if param["required"]:
                    params.append(f"<{param['name']}:{param['type']}>")
                else:
                    default_str = repr(param["default"]) if param["default"] is not None else "None"
                    params.append(f"[{param['name']}:{param['type']}={default_str}]")

            param_str = " ".join(params)
            description = method_info["description"] or "No description"

            print(f"  {method_name:20} {param_str:30} {description}")

        print(f"\nUsage: {prog_name} {handler_name} <method> [args...]")

    def _run_http(self, port: int):
        """
        Run HTTP mode with FastAPI + Swagger UI.

        Args:
            port: Port to listen on (default: 8000)
        """
        try:
            from .api_server import create_fastapi_app
            import uvicorn
        except ImportError:
            print("Error: FastAPI is not installed.")
            print("Install with: pip install smpub[http]")
            sys.exit(1)

        # Check if there are any OpenAPI handlers
        if not self._openapi_handlers:
            print("Warning: No handlers published with openapi=True")
            print("Publishing with cli=True, openapi=True to expose via HTTP")
            return

        # Create FastAPI app
        app = create_fastapi_app(
            self,
            title=f"{self.__class__.__name__} API",
            description=self.__class__.__doc__ or f"{self.__class__.__name__} API",
            version="0.1.0",
        )

        # Print startup info
        print(f"\n{self.__class__.__name__} - HTTP Mode")
        print(f"Starting server on http://localhost:{port}")
        print(f"Swagger UI available at http://localhost:{port}/docs")
        print(f"OpenAPI schema at http://localhost:{port}/openapi.json")
        print("\nPublished handlers:")
        for path, handler_info in self._openapi_handlers.items():
            handler_name = handler_info["name"]
            print(f"  {handler_name:15} -> {path}")
        print("\nPress Ctrl+C to stop\n")

        # Run server
        uvicorn.run(app, host="0.0.0.0", port=port)
