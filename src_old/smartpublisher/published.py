"""
Utilities for publishable handlers and API discovery.
"""

import inspect


def discover_api_json(target, recursive=False, switcher_name="api") -> dict:
    """
    Discover API schema from a handler (class or instance).

    Args:
        target: Class or instance to discover
        recursive: If True, include nested handlers (not yet implemented)
        switcher_name: Name of the Switcher class attribute (default: 'api')

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
    if not hasattr(target_class, switcher_name):
        return result

    switcher = getattr(target_class, switcher_name)
    prefix = getattr(switcher, "prefix", None) or ""

    # Get all registered methods using public API
    # Try new API first (smartswitch 0.9.1+)
    entries = []
    try:
        description = switcher.describe()
        if isinstance(description, dict) and "methods" in description:
            entries = list(description["methods"].keys())
    except (AttributeError, TypeError):
        pass

    # Fallback to old API (for backward compatibility and tests)
    if not entries:
        try:
            entries_result = switcher.entries() if callable(getattr(switcher, "entries", None)) else getattr(switcher, "entries", [])
            entries = list(entries_result) if entries_result else []
        except (AttributeError, TypeError):
            entries = []

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

        # Try to use pre-prepared metadata from PydanticPlugin (fast path)
        used_metadata = False
        if hasattr(switcher, '_methods') and isinstance(switcher._methods, dict) and method_key in switcher._methods:
            entry = switcher._methods[method_key]
            pydantic_meta = entry.metadata.get("pydantic", {})
            if pydantic_meta and "param_info" in pydantic_meta:
                # Use pre-extracted parameter info (no inspect!)
                method_info["parameters"] = pydantic_meta["param_info"]
                used_metadata = True

        # Fallback: extract signature if metadata not available
        if not used_metadata:
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

    This object is injected into handlers via the 'smpublisher' attribute
    and provides access to publisher features without polluting the
    handler's namespace.
    """

    __slots__ = ("parent_api", "_handler", "switcher_name")

    def __init__(self, handler, switcher_name="api"):
        """
        Initialize context for a handler.

        Args:
            handler: The handler instance this context is attached to
            switcher_name: Name of the Switcher class attribute (default: 'api')
        """
        self._handler = handler
        self.parent_api = None
        self.switcher_name = switcher_name

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
            >>> schema = handler.smpublisher.get_api_json()
            >>> print(schema['methods']['add']['parameters'])
            [{'name': 'key', 'type': 'str', 'required': True, 'default': None}]
        """
        if target is None:
            target = self._handler
        return discover_api_json(target, recursive=recursive, switcher_name=self.switcher_name)
