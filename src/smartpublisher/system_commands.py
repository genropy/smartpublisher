"""
SystemCommands - Business logic for Publisher introspection.

These are BUSINESS commands, not transport commands.
They work the same way on CLI, HTTP, or any other channel.

NO print statements - only structured data returns.
"""

from smartroute.core import Router, RoutedClass, route


class SystemCommands(RoutedClass):
    """
    System commands for Publisher introspection.

    These commands provide information about published handlers,
    available methods, etc. They are channel-agnostic.
    """

    def __init__(self, publisher):
        """
        Initialize SystemCommands.

        Args:
            publisher: Publisher instance
        """
        super().__init__()
        self.publisher = publisher
        # Router name must match @route target ("api")
        self.api = Router(self, name="api").plug("pydantic")

    @route("api")
    def list_handlers(self) -> dict:
        """
        List all published handlers.

        Returns:
            dict: Handler information
        """
        handlers = {}
        for name, meta in self.publisher.handler_members().items():
            instance = meta.get("instance")
            handler_info = {
                "class": instance.__class__.__name__ if instance else None,
                "has_api": hasattr(instance, "api") if instance else False,
            }

            # Get methods from SmartRoute API (single source of truth)
            if instance and hasattr(instance, "api"):
                schema = instance.api.describe()
                handler_info["methods"] = list(schema.get("methods", {}).keys())
            else:
                handler_info["methods"] = []

            handlers[name] = handler_info

        return {"total": len(handlers), "handlers": handlers}

    @route("api")
    def get_handler_info(self, handler_name: str) -> dict:
        """
        Get detailed information about a specific handler.

        Args:
            handler_name: Name of the handler

        Returns:
            dict: Handler details
        """
        handler = self.publisher.get_handler(handler_name)
        if handler is None:
            return {
                "error": f"Handler '{handler_name}' not found",
                "available": self.publisher.list_handlers(),
            }

        # Get API schema if available
        api_schema = None
        if hasattr(handler, "api"):
            api_schema = handler.api.describe()

        return {
            "name": handler_name,
            "class": handler.__class__.__name__,
            "docstring": handler.__class__.__doc__,
            "api_schema": api_schema,
        }

    @route("api")
    def get_api_tree(self) -> dict:
        """
        Get complete API tree structure.

        Returns:
            dict: Full API hierarchy
        """
        return self.publisher.api.describe()
