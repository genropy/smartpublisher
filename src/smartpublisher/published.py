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

from smartroute.core import Router, RoutedClass, route

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

        # Track handlers published by this app
        self.published_instances = {}

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

        # Publish system handler like any other handler
        self.published_instances['_system'] = system

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
        # Save instance
        self.published_instances[name] = handler_instance

        # Add handler as child using SmartRoute's add_child()
        # This creates hierarchical structure with instance binding
        if hasattr(handler_instance, 'api'):
            self.api.add_child(handler_instance, name=name)

        # Return structured result
        result = {
            "status": "published",
            "name": name,
            "handler_class": handler_instance.__class__.__name__
        }

        # Get methods from SmartRoute API
        if hasattr(handler_instance, 'api'):
            schema = handler_instance.api.describe()
            result["methods"] = list(schema.get("methods", {}).keys())
        else:
            result["methods"] = []

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
            "handlers": list(self.published_instances.keys())
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
