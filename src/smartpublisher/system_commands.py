"""
SystemCommands - Business logic for Publisher introspection.

These are BUSINESS commands, not transport commands.
They work the same way on CLI, HTTP, or any other channel.

NO print statements - only structured data returns.
"""

from smartroute.core import Router


class SystemCommands:
    """
    System commands for Publisher introspection.

    These commands provide information about published handlers,
    available methods, etc. They are channel-agnostic.
    """

    api = Router(name="system")

    def __init__(self, publisher):
        """
        Initialize SystemCommands.

        Args:
            publisher: Publisher instance
        """
        self.publisher = publisher

    @api
    def list_handlers(self) -> dict:
        """
        List all published handlers.

        Returns:
            dict: Handler information
        """
        handlers = {}
        for name, instance in self.publisher.published_instances.items():
            handler_info = {
                "class": instance.__class__.__name__,
                "has_api": hasattr(instance.__class__, 'api')
            }

            # Get methods from SmartRoute API (single source of truth)
            if hasattr(instance, 'api'):
                schema = instance.api.describe()
                handler_info["methods"] = list(schema.get("methods", {}).keys())
            else:
                handler_info["methods"] = []

            handlers[name] = handler_info

        return {
            "total": len(handlers),
            "handlers": handlers
        }

    @api
    def get_handler_info(self, handler_name: str) -> dict:
        """
        Get detailed information about a specific handler.

        Args:
            handler_name: Name of the handler

        Returns:
            dict: Handler details
        """
        if handler_name not in self.publisher.published_instances:
            return {
                "error": f"Handler '{handler_name}' not found",
                "available": list(self.publisher.published_instances.keys())
            }

        instance = self.publisher.published_instances[handler_name]

        # Get API schema if available
        api_schema = None
        if hasattr(instance, 'api'):
            api_schema = instance.api.describe()

        return {
            "name": handler_name,
            "class": instance.__class__.__name__,
            "docstring": instance.__class__.__doc__,
            "api_schema": api_schema
        }

    @api
    def get_api_tree(self) -> dict:
        """
        Get complete API tree structure.

        Returns:
            dict: Full API hierarchy
        """
        return self.publisher.api.describe()
