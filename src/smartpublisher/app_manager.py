from __future__ import annotations

"""AppManager - dynamic loader and router for published applications.

Responsibilities
----------------
- Load and instantiate application classes from a file spec
  (``/path/to/app.py[:ClassName]``, default class ``Main``) forwarding *args/**kwargs.
- Mount each instantiated app as a child of its own SmartRoute router (``api``),
  so when the publisher mounts AppManager under ``apps`` the apps are reachable as
  ``/apps/<name>/...`` across channels (CLI/HTTP/etc.).
- Track minimal restart metadata per app (spec, args, kwargs, module, class, path)
  to support listing and external state snapshots (persistence is handled by StateManager).
- Remove apps cleanly from the router and internal registries.

What it does NOT do
-------------------
- No autosave, persistence, or reload orchestration.
- No name validation beyond uniqueness (``add`` will raise if already present).
- No lifecycle hooks or thread-safety guarantees; assumed single-threaded use.

Side effects and constraints
----------------------------
- Importing an app executes top-level code of the target module.
- The spec must point to an existing Python file (not a package/directory).
- Uses the SmartRoute ``pydantic`` plug-in for request parsing/validation.

Primary operations
------------------
- ``add(name, spec, *args, **kwargs)``: load, instantiate, mount, and record restart data.
- ``remove(name)``: unmount and delete runtime + restart info (idempotent on missing returns an error).
- ``list()``: reflect current children from the router and return restart metadata for each.
- ``snapshot()``: return the restart payload used by StateManager when persisting state.
"""

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from typing import Any, Tuple

from smartroute import Router, RoutedClass, route


class AppManager(RoutedClass):
    """Load, register, and manage published applications."""

    def __init__(self, publisher):
        self.publisher = publisher
        self.api = Router(self, name="api").plug("pydantic")
        self.applications: dict[str, Any] = {}
        self.apps_restart_dict: dict[str, dict[str, Any]] = {}
        self._app_attrs: dict[str, str] = {}

    def snapshot(self) -> list[dict[str, Any]]:
        """
        Return minimal reload info for registered applications.

        Each entry contains name, spec, args, kwargs to recreate the app.
        """
        return [{"name": name, **params} for name, params in sorted(self.apps_restart_dict.items())]

    @route("api")
    def list(self) -> dict:
        """List registered applications."""
        children = self.api.members().get("children", {}) or {}
        apps_dict = {
            name: {"name": name, **self.apps_restart_dict.get(name, {})}
            for name in sorted(children.keys())
        }
        return {
            "total": len(children),
            "applications": list(apps_dict.values()),
            "apps": apps_dict,
        }

    @route("api")
    def add(self, name: str, spec: str, *app_args, **app_kwargs) -> dict:
        """Instantiate and publish an application."""
        if name in self.applications:
            raise ValueError(f"App '{name}' already registered")

        file_path, module_name, class_name = self._parse_spec(spec)
        app_class = self._import_class(file_path, class_name)
        app = app_class(*app_args, **app_kwargs)

        self.applications[name] = app
        attr_name = f"_app_{name.replace('/', '_')}"
        self._app_attrs[name] = attr_name
        setattr(self, attr_name, app)
        self.apps_restart_dict[name] = {
            "spec": spec,
            "args": list(app_args),
            "kwargs": dict(app_kwargs),
            "module": module_name,
            "class": class_name,
            "path": str(file_path),
        }
        self.api.attach_instance(app, name=name)

        return {"status": "registered", "name": name, **self.apps_restart_dict[name]}

    @route("api")
    def remove(self, name: str) -> dict:
        """Unregister a published application."""
        if name not in self.applications:
            return {
                "error": "App not found",
                "name": name,
                "available": list(self.applications.keys()),
            }

        app = self.applications.pop(name)
        self.api.detach_instance(app)
        attr_name = self._app_attrs.pop(name, None)
        if attr_name and hasattr(self, attr_name):
            delattr(self, attr_name)
        self.apps_restart_dict.pop(name, None)

        return {"status": "removed", "name": name}

    # ------------------------
    # Internal helpers
    # ------------------------
    def _parse_spec(self, spec: str) -> Tuple[Path, str, str]:
        if not spec:
            raise ValueError("Application specification cannot be empty")

        if ":" in spec:
            path_part, class_name = spec.rsplit(":", 1)
            class_name = class_name or "Main"
        else:
            path_part = spec
            class_name = "Main"

        file_path = Path(path_part).expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Path does not exist: {file_path}")
        if file_path.is_dir():
            raise ValueError(
                f"Application specification must reference a Python module file, got directory: {file_path}"
            )

        module_name = file_path.stem
        return file_path, module_name, class_name

    def _import_class(self, file_path: Path, class_name: str):
        module_name = f"smpub_app_{file_path.stem}_{abs(hash(file_path))}"
        loader = SourceFileLoader(module_name, str(file_path))
        spec = spec_from_loader(module_name, loader)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for '{file_path}'")

        module = module_from_spec(spec)
        loader.exec_module(module)
        try:
            return getattr(module, class_name)
        except AttributeError as exc:
            raise AttributeError(f"Module '{module_name}' has no class '{class_name}'") from exc
