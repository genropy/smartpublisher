from __future__ import annotations

"""AppManager - registry for published applications."""

from contextlib import contextmanager
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
        self._metadata: dict[str, dict[str, str]] = {}
        self._state: dict[str, dict[str, Any]] = {}

    @property
    def _autosave(self) -> bool:  # type: ignore[override]
        return bool(getattr(self.publisher, "_autosave", False))

    @_autosave.setter  # type: ignore[override]
    def _autosave(self, value: bool):
        self.publisher._autosave = bool(value)

    # ------------------------
    # Internal helpers
    # ------------------------
    def _detach_from_publisher(self, name: str):
        self.publisher.api._children.pop(name, None)

    def _clear_registry(self) -> None:
        for name in list(self.applications.keys()):
            self._detach_from_publisher(name)
        self.applications.clear()
        self._metadata.clear()
        self._state.clear()

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

    def load(self, spec: str, *args, **kwargs) -> tuple[Any, dict[str, str]]:
        """Load class referenced by spec and instantiate it."""
        file_path, module_name, class_name = self._parse_spec(spec)
        app_class = self._import_class(file_path, class_name)
        instance = app_class(*args, **kwargs)
        metadata = {
            "path": str(file_path),
            "module": module_name,
            "class": class_name,
        }
        return instance, metadata

    # ------------------------
    # API methods
    # ------------------------
    def snapshot(self) -> list[dict[str, Any]]:
        """Return a serializable snapshot of registered applications."""
        return [{"name": name, **state} for name, state in self._state.items()]

    @route("api")
    def list(self) -> dict:
        """List registered applications."""
        apps_dict = {name: self._metadata.get(name, {}) for name in sorted(self.applications.keys())}
        return {
            "total": len(self.applications),
            "applications": [
                {"name": name, **self._metadata.get(name, {})}
                for name in sorted(self.applications.keys())
            ],
            "apps": apps_dict,
        }

    @route("api")
    def add(self, name: str, spec: str, *app_args, **app_kwargs) -> dict:
        """Instantiate and publish an application."""
        if name in self.applications:
            raise ValueError(f"App '{name}' already registered")

        if name.startswith("/"):
            raise ValueError("App names cannot start with '/' because those are reserved commands")

        app, metadata = self.load(spec, *app_args, **app_kwargs)

        self.applications[name] = app
        self._metadata[name] = metadata
        self._state[name] = {
            "spec": spec,
            "args": list(app_args),
            "kwargs": dict(app_kwargs),
        }
        self.publisher.api.add_child(app, name=name)

        if self._autosave:
            self.savestate()

        return {"status": "registered", "name": name, **self._metadata[name]}

    @route("api")
    def remove(self, name: str) -> dict:
        """Unregister a published application."""
        if name not in self.applications:
            return {
                "error": "App not found",
                "name": name,
                "available": list(self.applications.keys()),
            }

        self.applications.pop(name)
        self._detach_from_publisher(name)
        self._metadata.pop(name, None)
        self._state.pop(name, None)

        if self._autosave:
            self.savestate()

        return {"status": "removed", "name": name}

    @route("api")
    def get(self, name: str):
        """Return runtime app instance."""
        if name not in self.applications:
            available = list(self.applications.keys())
            raise ValueError(
                f"App '{name}' not registered. "
                f"Available: {', '.join(available) if available else 'none'}"
            )
        return self.applications[name]

    @route("api")
    def unload(self, app_name: str):
        """Unregister an application and discard its state."""
        if app_name not in self.applications:
            return {"error": f"App '{app_name}' not registered"}
        self.remove(app_name)
        return {"status": "unloaded", "app": app_name}

    def savestate(self, path: str | Path | None = None) -> dict:
        """Save current registry state to file (delegates to publisher)."""
        return self.publisher.savestate(path)

    def restore(self, payload: dict, skip_missing: bool = False) -> dict:
        """
        Restore applications from a snapshot payload.

        Args:
            payload: Dict containing at least an ``apps`` list.
            skip_missing: If true, skip entries that fail to load.
        """
        if not isinstance(payload, dict) or "apps" not in payload or not isinstance(payload["apps"], list):
            return {"error": "Malformed state: missing 'apps' list"}

        skipped = []
        with self._suspend_autosave():
            self._clear_registry()
            for entry in payload.get("apps", []):
                try:
                    name = entry["name"]
                    spec = entry["spec"]
                    args = entry.get("args", [])
                    kwargs = entry.get("kwargs", {})
                    self.add(name, spec, *args, **kwargs)
                except Exception as exc:
                    if skip_missing:
                        skipped.append({"entry": entry, "error": str(exc)})
                        continue
                    raise

        if self._autosave:
            self.savestate()

        return {"loaded": len(self.applications), "skipped": skipped}

    def autosave(self, enabled: bool | None = None) -> dict:
        """Get/set autosave flag."""
        if enabled is not None:
            self._autosave = bool(enabled)
        return {"autosave": self._autosave}

    @contextmanager
    def _suspend_autosave(self):
        prev = self._autosave
        self._autosave = False
        try:
            yield
        finally:
            self._autosave = prev
