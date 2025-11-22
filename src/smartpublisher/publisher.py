from __future__ import annotations

"""Publish and orchestrate SmartRoute applications at runtime.

Public API exported
-------------------
- class ``Publisher``: coordinator and root SmartRoute handler.
- function ``get_publisher``: singleton accessor.

External dependencies
---------------------
- ``smartroute`` for routing and CLI/HTTP exposure.
- ``importlib.machinery.SourceFileLoader`` for loading standalone Python files.
- ``pathlib.Path`` and ``json`` for filesystem and state persistence.

Invariants and limitations
--------------------------
- Registry is in-memory; persistence is opt-in via ``/savestate`` and
  ``/loadstate`` using a JSON snapshot. Applications are lost between runs
  unless explicitly saved/loaded.
- Application specs must point to a single Python file
  ``/path/to/module.py[:ClassName]``; no packages or directories. The module
  is loaded via ``SourceFileLoader`` without mutating ``sys.path``. Relative
  imports inside the module will fail unless resolvable without package
  context.
- Names are unique, cannot start with ``/`` (reserved for root commands), and
  may otherwise coincide with root command names because the slash disambiguates.
- Operations are not thread-safe; assumed single-process, single-thread use.

Side effects
------------
- ``/add`` and ``/loadstate`` import arbitrary files; they may execute module
  top-level code.
- ``/savestate`` writes a JSON file to the chosen path (default
  ``~/.smartlibs/publisher/state.json``).

Extension points
----------------
- New root commands can be added via ``@route("api", name="/...")`` on the
  Publisher.
- Channels register against ``ChanRegistry``; CLI/HTTP are wired by default.

Typical usage
-------------
1. Start Publisher and add an app:
   ``/add demo /tmp/app.py:Main`` (extra args are forwarded to the constructor).
2. List published apps: ``/list``.
3. Scopes/channels: the root router is wired with ``PublishPlugin`` plus
   ``pydantic``; handlers/apps can attach scope/channel metadata.
4. Save current state: ``/savestate [path]``.
5. Restore from file: ``/loadstate [path]`` (recreates apps via ``/add``).
6. Manage autosave: ``/autosave [true|false]``.
"""

from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import json
from pathlib import Path
from typing import Any, Tuple

from smartroute import Router, RoutedClass, route
from .chan_registry import ChanRegistry
from .smartroute_plugins import PublishPlugin  # noqa: F401 - needed for plugin registration


class AppManager:
    """Load and instantiate publishable applications from standalone files."""

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


class Publisher(RoutedClass):
    """
    Coordinate published apps and expose root SmartRoute commands.

    Responsibilities:
    - register/unregister applications in-memory
    - expose root commands for management
    - orchestrate channels (CLI/HTTP) via ``ChanRegistry``
    - optionally persist/restore state snapshots

    Not thread-safe; intended for single-process use.
    """

    def __init__(
        self,
        registry_path: Path = None,
        use_global: bool = False,
        state_path: Path | None = None,
        autosave: bool = True,
    ):
        """
        Build a Publisher coordinator.

        Args:
            registry_path: Unused (kept for backward signature compatibility).
            use_global: Unused flag (kept for compatibility).
            state_path: Target file for /savestate and autosave (default:
                ~/.smartlibs/publisher/state.json).
            autosave: Enable automatic save on mutations.
        """
        super().__init__()
        self.api = Router(self, name="root").plug("pydantic").plug("publish")

        self.applications: dict[str, Any] = {}
        self._metadata: dict[str, dict[str, str]] = {}
        self._state: dict[str, dict[str, Any]] = {}
        self._autosave = autosave
        self.state_path = (
            Path(state_path).expanduser().resolve()
            if state_path is not None
            else Path.home() / ".smartlibs" / "publisher" / "state.json"
        )
        self.app_manager = AppManager()

        self.chan_registry = ChanRegistry(self)
        # Expose channel registry as root command "/channel"
        self.api.add_child(self.chan_registry, name="/channel")

    @route("api", name="/serve")
    def serve(self, channel: str = "http", port: int | None = None, **options):
        """
        Start a Publisher channel (e.g., HTTP).

        Args:
            channel: registered channel name (e.g., http, cli)
            port: optional port (if supported by the channel)
            **options: additional channel-specific parameters
        """
        chan_name = (channel or "").lower()
        try:
            chan = self.get_channel(chan_name)
        except KeyError:
            return {
                "error": f"Channel '{chan_name}' not available",
                "available": list(self.chan_registry.channels.keys()),
            }

        run_opts = dict(options)
        if port is not None:
            run_opts.setdefault("port", port)

        # run() may block (e.g., HTTP); let exceptions propagate
        result = chan.run(**run_opts)
        return {"status": "started", "channel": chan_name, "options": run_opts, "result": result}

    @route("api", name="/quit")
    def quit(self):
        """Placeholder quit command exposed via API."""
        return {
            "status": "disabled",
            "message": "Quit command not wired yet",
        }

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------
    def _detach_from_publisher(self, name: str):
        self.api._children.pop(name, None)

    @route("api", name="/add")
    def add(self, name: str, spec: str, *app_args, **app_kwargs) -> dict:
        """
        Instantiate and publish an application.

        Args:
            name: Registry name for the application.
            spec: Filesystem spec in the form "/path/to/module.py[:ClassName]".
            *app_args: Positional arguments forwarded to the app constructor.
            **app_kwargs: Keyword arguments forwarded to the app constructor.
        """
        if name in self.applications:
            raise ValueError(f"App '{name}' already registered")

        if name.startswith("/"):
            raise ValueError("App names cannot start with '/' because those are reserved commands")

        app, metadata = self.app_manager.load(spec, *app_args, **app_kwargs)

        self.applications[name] = app
        self._metadata[name] = metadata
        self._state[name] = {
            "spec": spec,
            "args": list(app_args),
            "kwargs": dict(app_kwargs),
        }
        self.api.add_child(app, name=name)

        if self._autosave:
            self.savestate()

        return {"status": "registered", "name": name, **self._metadata[name]}

    @route("api", name="/remove")
    def remove(self, name: str) -> dict:
        """Unregisters a published application."""
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

    @route("api", name="/list")
    def list(self) -> dict:
        """Lists published applications."""
        return {"total": len(self.applications), "apps": dict(self._metadata)}

    @route("api", name="/getapp")
    def getapp(self, name: str) -> dict:
        """Returns stored metadata for an app."""
        if name not in self.applications:
            return {
                "error": "App not found",
                "name": name,
                "available": list(self.applications.keys()),
            }

        return {"name": name, **self._metadata[name]}

    @route("api", name="/unload_app")
    def unload_app(self, app_name: str):
        """
        Unload an application.

        Args:
            app_name: Registered application name
        """
        if app_name not in self.applications:
            return {"error": f"App '{app_name}' not registered"}

        self.remove(app_name)
        return {"status": "unloaded", "app": app_name}

    @route("api", name="/savestate")
    def savestate(self, path: str | None = None) -> dict:
        """Persist current registry to JSON file."""
        dest = self._resolve_state_path(path)
        self._write_state(dest)
        return {
            "status": "saved",
            "path": str(dest),
            "total": len(self._state),
        }

    @route("api", name="/loadstate")
    def loadstate(self, path: str | None = None, skip_missing: bool = False) -> dict:
        """
        Rebuild registry from a JSON snapshot.

        Args:
            path: Override state file path (default: configured state_path).
            skip_missing: If true, skip entries whose spec path is missing
                instead of failing the entire load.
        """
        source = self._resolve_state_path(path)
        if not source.exists():
            return {"error": "State file not found", "path": str(source)}

        try:
            snapshot = json.loads(source.read_text())
        except Exception as exc:
            return {"error": f"Invalid state file: {exc}", "path": str(source)}

        if "apps" not in snapshot or not isinstance(snapshot["apps"], list):
            return {"error": "Malformed state: missing 'apps' list", "path": str(source)}

        failed = []
        with self._suspend_autosave():
            self._clear_registry()
            for entry in snapshot["apps"]:
                try:
                    name = entry["name"]
                    spec = entry["spec"]
                    args = entry.get("args", [])
                    kwargs = entry.get("kwargs", {})
                    self.add(name, spec, *args, **kwargs)
                except Exception as exc:
                    if skip_missing:
                        failed.append({"entry": entry, "error": str(exc)})
                        continue
                    raise

        if self._autosave:
            self.savestate()

        return {
            "status": "loaded",
            "path": str(source),
            "total": len(self.applications),
            "skipped": failed,
        }

    @route("api", name="/autosave")
    def autosave(self, enabled: bool | None = None) -> dict:
        """
        Get or set autosave mode.

        Args:
            enabled: Optional flag to update autosave setting.
        """
        if enabled is not None:
            self._autosave = bool(enabled)
        return {"autosave": self._autosave}

    def load_app(self, name: str):
        """
        Return runtime app instance.
        """
        if name not in self.applications:
            available = list(self.applications.keys())
            raise ValueError(
                f"App '{name}' not registered. "
                f"Available: {', '.join(available) if available else 'none'}"
            )
        return self.applications[name]

    def get_channel(self, channel_name: str):
        """Return channel instance by name."""
        return self.chan_registry.get(channel_name)

    def add_channel(self, channel_name: str, channel_instance):
        """Register or override a channel instance."""
        self.chan_registry.channels[channel_name] = channel_instance

    def run_cli(self, args: list | None = None):
        """CLI entry point - delegates to CLI channel."""
        cli_channel = self.get_channel("cli")
        cli_channel.run(args)

    def run_http(self, port: int = 8000, **kwargs):
        """Run HTTP channel."""
        http_channel = self.get_channel("http")
        http_channel.run(port=port, **kwargs)

    # ------------------------------------------------------------------
    # Helper APIs used by channels
    # ------------------------------------------------------------------
    def handler_members(self, channel: str | None = None) -> dict:
        """Return immediate child handlers metadata (optionally filtered by channel)."""
        return self.api.members(channel=channel).get("children", {})

    def get_handler(self, name: str, channel: str | None = None):
        """Return handler instance by name if available (respecting channel filter)."""
        meta = self.handler_members(channel=channel).get(name)
        if not meta:
            return None
        return meta.get("instance")

    def list_handlers(self, channel: str | None = None) -> list:
        """Return list of published handler names."""
        return list(self.handler_members(channel=channel).keys())

    def get_handlers(self, channel: str | None = None) -> dict:
        """Return mapping name -> handler instance."""
        handlers = {}
        for name, meta in self.handler_members(channel=channel).items():
            instance = meta.get("instance")
            if instance is not None:
                handlers[name] = instance
        return handlers

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

    @contextmanager
    def _suspend_autosave(self):
        prev = self._autosave
        self._autosave = False
        try:
            yield
        finally:
            self._autosave = prev


# # Singleton instance for convenience
_default_publisher = None


def get_publisher(use_global: bool = False) -> Publisher:
    """
    Get the default Publisher instance.

    Args:
        use_global: Use global registry

    Returns:
        Publisher instance
    """
    global _default_publisher

    if _default_publisher is None:
        _default_publisher = Publisher(use_global=use_global)

    return _default_publisher


# Module-level entry point for CLI
def main():
    """Entry point for smpub command."""
    publisher = Publisher()
    publisher.run_cli()


if __name__ == "__main__":
    main()
