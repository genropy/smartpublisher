from __future__ import annotations

"""AppManager - registry for published applications."""

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import json
from pathlib import Path
from typing import Any, Tuple

from smartroute import Router, RoutedClass, route


class AppManager(RoutedClass):
    """Load, register, and manage published applications."""

    def __init__(self, publisher, *, autosave: bool = True, state_path: Path | None = None):
        self.publisher = publisher
        self.api = Router(self, name="api").plug("pydantic")
        self.applications: dict[str, Any] = {}
        self._metadata: dict[str, dict[str, str]] = {}
        self._state: dict[str, dict[str, Any]] = {}
        self._autosave = autosave
        self.state_path = (
            Path(state_path).expanduser().resolve()
            if state_path is not None
            else Path.home() / ".smartlibs" / "publisher" / "state.json"
        )

    # ------------------------
    # Internal helpers
    # ------------------------
    def _detach_from_publisher(self, name: str):
        self.publisher.api._children.pop(name, None)

    def _resolve_state_path(self, path: str | Path | None) -> Path:
        return Path(path).expanduser().resolve() if path else self.state_path

    def _write_state(self, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "autosave": self._autosave,
            "apps": [{"name": name, **state} for name, state in self._state.items()],
        }
        dest.write_text(json.dumps(payload, indent=2))

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
    @route("api")
    def list(self) -> dict:
        """List registered applications."""
        return {
            "total": len(self.applications),
            "applications": [
                {"name": name, **self._metadata.get(name, {})}
                for name in sorted(self.applications.keys())
            ],
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
        """Save current registry state to file."""
        dest = self._resolve_state_path(path)
        self._write_state(dest)
        return {"saved": str(dest), "apps": len(self.applications)}

    def loadstate(self, path: str | Path | None = None, skip_missing: bool = False) -> dict:
        """Load registry state from file."""
        source = self._resolve_state_path(path)
        if not source.exists():
            raise FileNotFoundError(f"State file not found: {source}")

        with open(source, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        self._clear_registry()
        self._autosave = bool(data.get("autosave", True))

        for entry in data.get("apps", []):
            name = entry.get("name")
            spec = entry.get("spec")
            args = entry.get("args", [])
            kwargs = entry.get("kwargs", {})
            try:
                self.add(name, spec, *args, **kwargs)
            except Exception:
                if not skip_missing:
                    raise
        return {"loaded": len(self.applications)}

    def autosave(self, enabled: bool | None = None) -> dict:
        """Get/set autosave flag."""
        if enabled is not None:
            self._autosave = bool(enabled)
        return {"autosave": self._autosave}
