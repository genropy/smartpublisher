"""
AppRegistry - Registry for managing Published applications.

This is a handler with Switcher, just like any business handler.
Commands are exposed via @api decorator.

Key principles:
- Uses ONLY SmartSwitch APIs
- Returns structured data (NO print!)
- Commands work on CLI and HTTP
"""

import sys
import json
from pathlib import Path
from smartroute.core import Router, RoutedClass, route


class AppRegistry:
    """
    Registry for managing Published applications.

    This is a handler with Switcher - commands are exposed via @api.
    Accessible via: smpub .apps <command>

    Commands:
        add: Register an app
        remove: Unregister an app
        list: List all registered apps
        getapp: Get info about a specific app
    """

    api = Router(name="apps").plug("pydantic")

    def __init__(self, registry_path: Path):
        """
        Initialize AppRegistry.

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = registry_path
        self._data = self._load()

    def _load(self) -> dict:
        """Load registry from JSON file."""
        if not self.registry_path.exists():
            return {"apps": {}}

        with open(self.registry_path) as f:
            return json.load(f)

    def _save(self):
        """Save registry to JSON file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self._data, f, indent=2)

    @api
    def add(self, name: str, path: str, module: str = "main", class_name: str = "App") -> dict:
        """
        Register an app in the registry.

        Args:
            name: App name (used in CLI)
            path: Path to app directory
            module: Python module name (default: "main")
            class_name: Class name to instantiate (default: "App")

        Returns:
            dict: Registration result
        """
        # Validate path
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            return {
                "error": f"Path does not exist",
                "path": str(path_obj)
            }

        # Store app info
        self._data["apps"][name] = {
            "path": str(path_obj),
            "module": module,
            "class": class_name
        }
        self._save()

        return {
            "status": "registered",
            "name": name,
            "path": str(path_obj),
            "module": module,
            "class": class_name
        }

    @api
    def remove(self, name: str) -> dict:
        """
        Unregister an app from the registry.

        Args:
            name: App name

        Returns:
            dict: Removal result
        """
        if name not in self._data["apps"]:
            return {
                "error": f"App not found",
                "name": name,
                "available": list(self._data["apps"].keys())
            }

        app_info = self._data["apps"][name]
        del self._data["apps"][name]
        self._save()

        return {
            "status": "removed",
            "name": name,
            "path": app_info["path"]
        }

    @api
    def list(self) -> dict:
        """
        List all registered apps.

        Returns:
            dict: Registry contents
        """
        return {
            "total": len(self._data["apps"]),
            "apps": self._data["apps"]
        }

    @api
    def getapp(self, name: str) -> dict:
        """
        Get information about a specific app.

        Args:
            name: App name

        Returns:
            dict: App information
        """
        if name not in self._data["apps"]:
            return {
                "error": f"App not found",
                "name": name,
                "available": list(self._data["apps"].keys())
            }

        return {
            "name": name,
            **self._data["apps"][name]
        }

    def load(self, name: str):
        """
        Load and instantiate an app.

        This method is NOT decorated with @api because it returns
        a Published instance, not a dict.

        Args:
            name: App name

        Returns:
            Published instance

        Raises:
            ValueError: If app not found
        """
        if name not in self._data["apps"]:
            available = list(self._data["apps"].keys())
            raise ValueError(
                f"App '{name}' not found in registry. "
                f"Available: {', '.join(available) if available else 'none'}"
            )

        app_info = self._data["apps"][name]
        app_path = Path(app_info["path"])

        # Add to sys.path if not already there
        if str(app_path) not in sys.path:
            sys.path.insert(0, str(app_path))

        # Import and instantiate
        import importlib
        try:
            mod = importlib.import_module(app_info["module"])
        except ImportError as e:
            raise ImportError(
                f"Cannot import module '{app_info['module']}' from {app_path}. "
                f"Error: {e}"
            )

        try:
            app_class = getattr(mod, app_info["class"])
        except AttributeError:
            raise AttributeError(
                f"Module '{app_info['module']}' has no class '{app_info['class']}'"
            )

        # Instantiate and return Published instance
        return app_class()


# Factory functions for registry discovery

def get_local_registry() -> AppRegistry:
    """Get local registry (.published in current directory)."""
    registry_path = Path.cwd() / ".published"
    return AppRegistry(registry_path)


def get_global_registry() -> AppRegistry:
    """Get global registry (~/.smartlibs/publisher/registry.json)."""
    registry_path = Path.home() / ".smartlibs" / "publisher" / "registry.json"
    return AppRegistry(registry_path)


def discover_app(name: str) -> AppRegistry:
    """
    Discover app in local or global registry.

    Tries local first, then global.

    Args:
        name: App name

    Returns:
        AppRegistry instance containing the app

    Raises:
        ValueError: If app not found in either registry
    """
    # Try local first
    local_reg = get_local_registry()
    if name in local_reg._data["apps"]:
        return local_reg

    # Try global
    global_reg = get_global_registry()
    if name in global_reg._data["apps"]:
        return global_reg

    # Not found
    raise ValueError(
        f"App '{name}' not found in local or global registry"
    )
