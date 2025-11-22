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
import json
from pathlib import Path
from typing import Any, Tuple

from smartroute import Router, RoutedClass, route
from .chan_registry import ChanRegistry
from .smartroute_plugins import PublishPlugin  # noqa: F401 - needed for plugin registration
from .app_manager import AppManager


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
        # Root router for business/system commands
        self.api = Router(self, name="api").plug("pydantic").plug("publish")

        self.applications: dict[str, Any] = {}
        self._metadata: dict[str, dict[str, str]] = {}
        self._state: dict[str, dict[str, Any]] = {}
        self._autosave = autosave
        self.state_path = (
            Path(state_path).expanduser().resolve()
            if state_path is not None
            else Path.home() / ".smartlibs" / "publisher" / "state.json"
        )
        self.app_manager = AppManager(self, autosave=autosave, state_path=state_path)
        # Aliases for backward compatibility
        self.applications = self.app_manager.applications
        self._metadata = self.app_manager._metadata
        self._state = self.app_manager._state
        self._autosave = self.app_manager._autosave
        self.state_path = self.app_manager.state_path

        self.chan_registry = ChanRegistry(self)
        # Expose channel registry as root command "/channel"
        self.api.add_child(self.chan_registry, name="/channel")
        # Expose apps management as "/apps"
        self.api.add_child(self.app_manager, name="/apps")

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
        """Proxy to AppManager.add."""
        return self.app_manager.add(name, spec, *app_args, **app_kwargs)

    @route("api", name="/remove")
    def remove(self, name: str) -> dict:
        """Proxy to AppManager.remove."""
        return self.app_manager.remove(name)

    @route("api", name="/list")
    def list(self) -> dict:
        """Lists published applications."""
        return self.app_manager.list()

    @route("api", name="/getapp")
    def getapp(self, name: str) -> dict:
        """Returns stored metadata for an app."""
        if name not in self.applications:
            return {
                "error": "App not found",
                "name": name,
                "available": list(self.applications.keys()),
            }
        meta = self._metadata.get(name, {})
        return {"name": name, **meta}

    @route("api", name="/unload_app")
    def unload_app(self, app_name: str):
        """
        Unload an application.

        Args:
            app_name: Registered application name
        """
        return self.app_manager.unload(app_name)

    @route("api", name="/savestate")
    def savestate(self, path: str | None = None) -> dict:
        """Persist current registry to JSON file."""
        dest = self.app_manager._resolve_state_path(path)
        self.app_manager._write_state(dest)
        return {"status": "saved", "path": str(dest), "total": len(self._state)}

    @route("api", name="/loadstate")
    def loadstate(self, path: str | None = None, skip_missing: bool = False) -> dict:
        """
        Rebuild registry from a JSON snapshot.

        Args:
            path: Override state file path (default: configured state_path).
            skip_missing: If true, skip entries whose spec path is missing
                instead of failing the entire load.
        """
        result = self.app_manager.loadstate(path, skip_missing=skip_missing)
        return {"status": "loaded", **result}

    @route("api", name="/autosave")
    def autosave(self, enabled: bool | None = None) -> dict:
        """
        Get or set autosave mode.

        Args:
            enabled: Optional flag to update autosave setting.
        """
        return self.app_manager.autosave(enabled)

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
