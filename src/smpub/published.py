"""
PublishedClass - Mixin and utilities for publishable handlers.
"""

import inspect


def discover_api_json(target, recursive=False) -> dict:
    """
    Discover API schema from a handler (class or instance).

    Args:
        target: Class or instance to discover
        recursive: If True, include nested handlers (not yet implemented)

    Returns:
        {
            "class": "ClassName",
            "description": "Class docstring",
            "methods": {
                "method_name": {
                    "description": "Method docstring",
                    "parameters": [
                        {
                            "name": "param_name",
                            "type": "str",
                            "required": True,
                            "default": None
                        }
                    ]
                }
            }
        }
    """
    # Get class from instance if needed
    if not inspect.isclass(target):
        target_class = target.__class__
    else:
        target_class = target

    result = {
        "class": target_class.__name__,
        "description": (target_class.__doc__ or "").strip(),
        "methods": {},
    }

    # Check if class has a Switcher API
    if not hasattr(target_class, "api"):
        return result

    switcher = target_class.api
    prefix = switcher.prefix if hasattr(switcher, "prefix") else ""

    # Get all registered methods
    entries = switcher.entries() if hasattr(switcher, "entries") else []

    for method_key in entries:
        # method_key is the display name (without prefix)
        # We need to construct the full method name with prefix
        full_method_name = f"{prefix}{method_key}" if prefix else method_key
        display_name = method_key

        # Get the actual method
        if not hasattr(target_class, full_method_name):
            continue

        method = getattr(target_class, full_method_name)

        # Extract method info
        method_info = {
            "description": (method.__doc__ or "").strip().split("\n")[0],
            "parameters": [],
        }

        # Get signature
        try:
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Extract type annotation
                param_type = "Any"
                if param.annotation != inspect.Parameter.empty:
                    param_type = (
                        param.annotation.__name__
                        if hasattr(param.annotation, "__name__")
                        else str(param.annotation)
                    )

                # Check if required
                required = param.default == inspect.Parameter.empty
                default = None if required else param.default

                method_info["parameters"].append(
                    {
                        "name": param_name,
                        "type": param_type,
                        "required": required,
                        "default": default,
                    }
                )
        except Exception:
            # If signature extraction fails, just skip parameters
            pass

        result["methods"][display_name] = method_info

    return result


class PublisherContext:
    """
    Context object providing publisher-related functionality to handlers.

    This object is injected into handlers via the 'publisher' attribute
    and provides access to publisher features without polluting the
    handler's namespace.
    """

    __slots__ = ("parent_api", "_handler")

    def __init__(self, handler):
        """
        Initialize context for a handler.

        Args:
            handler: The handler instance this context is attached to
        """
        self._handler = handler
        self.parent_api = None

    def get_api_json(self, target=None, recursive=False) -> dict:
        """
        Get API schema as JSON.

        Args:
            target: Target for discovery. If None, uses self._handler.
                   Can be a class or instance.
            recursive: If True, include nested handlers (not yet implemented)

        Returns:
            Dictionary containing API schema with methods, parameters, etc.

        Example:
            >>> schema = handler.publisher.get_api_json()
            >>> print(schema['methods']['add']['parameters'])
            [{'name': 'key', 'type': 'str', 'required': True, 'default': None}]
        """
        if target is None:
            target = self._handler
        return discover_api_json(target, recursive=recursive)


class PublishedClass:
    """
    Optional mixin for handlers that use __slots__.

    This class only adds a 'publisher' slot. If your handler doesn't use
    __slots__, you don't need to inherit from this class - the Publisher
    will inject the 'publisher' attribute dynamically.

    Example with __slots__:
        class MyHandler(PublishedClass):
            __slots__ = ('data', 'registry')  # Your custom slots
            api = Switcher(prefix='my_')

            def __init__(self):
                self.data = {}
                self.registry = {}

            @api
            def my_add(self, key: str):
                self.data[key] = None

    Example without __slots__ (no inheritance needed):
        class MyHandler:
            api = Switcher(prefix='my_')

            def __init__(self):
                self.data = {}

            @api
            def my_add(self, key: str):
                self.data[key] = None
    """

    __slots__ = ("publisher",)
