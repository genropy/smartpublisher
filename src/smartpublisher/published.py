"""
PublishedClass - Mixin for publishable applications.

This is the base class that user apps inherit from.
Each app has its own root Router and handlers.

Example:
    class MyApp(PublishedClass):
        def on_init(self):
            self.publish("shop", ShopHandler())
            self.publish("users", UsersHandler())
"""

from smartroute.core import Router, RoutedClass

# Try relative import first (when used as package)
# Fall back to absolute import (when run directly)
try:
    from .system_commands import SystemCommands
except ImportError:
    from system_commands import SystemCommands


class PublishedClass(RoutedClass):
    """
    Mixin for publishable applications.

    User apps inherit from this class and get:
    - Root Router for business logic (self.api)
    - publish() method to register handlers
    - System commands for introspection (_system)
    - Lifecycle hooks

    Each app has its own isolated Router tree with instance binding.
    The Publisher connects multiple apps together.
    """

    # Router with pydantic plugin - applied at class level
    api = Router(name="root").plug("pydantic")

    def __init__(self):
        """Initialize PublishedClass with its own root Router."""
        # Note: plugins are applied at class level on the Router descriptor
        # self.api is now a BoundRouter instance with plugins already configured

        # Manual handlers without router
        self._manual_handlers: dict[str, object] = {}

        # Reference to Publisher (set when registered)
        self._publisher = None

        # System commands for app introspection
        self._init_system_commands()

        # Call user hook for app-specific initialization
        if hasattr(self, "on_init") and callable(self.on_init):
            self.on_init()

    def _init_system_commands(self):
        """Initialize system commands for app introspection."""
        # System commands provide info about THIS app
        system = SystemCommands(self)

        # Add system handler as child using SmartRoute's add_child()
        if hasattr(system, 'api'):
            self.api.add_child(system, name="_system")

    def publish(self, name: str, handler_instance, **options):
        """
        Publish a handler in this app.

        Args:
            name: Handler name
            handler_instance: Handler object with Router (should be RoutedClass)
            **options: Future options (metadata, etc.)

        Returns:
            dict: Publication result
        """
        # Add handler as child using SmartRoute's add_child()
        # This creates hierarchical structure with instance binding
        handler_router = getattr(handler_instance, 'api', None)
        if handler_router is not None:
            try:
                self.api.add_child(handler_router, name=name)
            except TypeError as exc:
                # Ignore mocks/objects without real Router descriptors
                if "Router descriptor" not in str(exc):
                    raise
            else:
                self._manual_handlers.pop(name, None)
        else:
            self._manual_handlers[name] = handler_instance

        # Return structured result
        result = {
            "status": "published",
            "name": name,
            "handler_class": handler_instance.__class__.__name__
        }

        # Get methods from SmartRoute API
        methods = []
        handler_api = getattr(handler_instance, 'api', None)
        if handler_api and hasattr(handler_api, 'describe'):
            try:
                schema = handler_api.describe()
            except TypeError:
                schema = None
            if isinstance(schema, dict):
                methods = list(schema.get("methods", {}).keys())

        result["methods"] = methods

        return result

    def _set_publisher(self, publisher):
        """
        Set reference to Publisher (called during registration).

        This allows the app to communicate with the Publisher.

        Args:
            publisher: Publisher instance
        """
        self._publisher = publisher

    def smpub_on_add(self):
        """
        Lifecycle hook called when app is registered with Publisher.

        Override in subclass for custom initialization.

        Returns:
            dict: Registration result
        """
        return {
            "message": f"{self.__class__.__name__} registered successfully",
            "handlers": self.list_handlers()
        }

    def smpub_on_remove(self):
        """
        Lifecycle hook called when app is unregistered from Publisher.

        Override in subclass for custom cleanup.

        Returns:
            dict: Cleanup result
        """
        return {
            "message": f"{self.__class__.__name__} unregistered"
        }

    def handler_members(self) -> dict:
        """Return runtime SmartRoute members."""
        members = dict(self.api.members().get('children', {}))
        for name, instance in self._manual_handlers.items():
            members[name] = {
                "name": name,
                "router": None,
                "instance": instance,
                "handlers": {},
                "children": {}
            }
        return members

    def get_handler(self, name: str):
        """Return handler instance by name."""
        return self.handler_members().get(name, {}).get('instance')

    def list_handlers(self) -> list:
        """Return list of handler names."""
        return list(self.handler_members().keys())

    def get_handlers(self) -> dict:
        """Return mapping name -> handler instance."""
        return {
            name: meta.get('instance')
            for name, meta in self.handler_members().items()
            if meta.get('instance') is not None
        }

    @property
    def published_instances(self) -> dict:
        """Backward-compatible view of published handlers."""
        return self.get_handlers()
