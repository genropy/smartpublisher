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

from pathlib import Path
from typing import Any

import json

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

        # Autosave flag lives on the publisher
        self._autosave = bool(autosave)

        self.state_path = (
            Path(state_path).expanduser().resolve()
            if state_path is not None
            else Path.home() / ".smartlibs" / "publisher" / "state.json"
        )

        self.app_manager = AppManager(self)
        # Aliases for backward compatibility
        self.applications = self.app_manager.applications
        self._metadata = self.app_manager._metadata
        self._state = self.app_manager._state

        self.chan_registry = ChanRegistry(self)
        # Expose channel registry as root command "channel"
        self.api.add_child(self.chan_registry, name="channel")
        # Expose apps management as "apps"
        self.api.add_child(self.app_manager, name="apps")

    @route("api")
    def serve(self, channel: str = "http", port: int | None = None, **options):
        """
        Start a Publisher channel (e.g., HTTP).

        Args:
            channel: registered channel name (e.g., http, cli)
            port: optional port (if supported by the channel)
            **options: additional channel-specific parameters
        """
        return self.api.call("channel.run", name=channel, port=port, **options)

    @route("api")
    def quit(self):
        """Placeholder quit command exposed via API."""
        return {
            "status": "disabled",
            "message": "Quit command not wired yet",
        }

    @route("api")
    def add_application(self, name: str, spec: str, *app_args, **app_kwargs) -> dict:
        """Route-exposed alias to add an application."""
        return self.api.call("apps.add", name=name, spec=spec, *app_args, **app_kwargs)

    @route("api")
    def savestate(self, path: str | None = None) -> dict:
        """
        Persist current state to JSON file.

        The publisher aggregates state from managed apps and channels
        and writes a single snapshot.
        """
        dest = self._resolve_state_path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": 1,
            "autosave": self._autosave,
            "apps": self.app_manager.snapshot(),
            "channels": self.chan_registry.snapshot(),
        }

        dest.write_text(json.dumps(payload, indent=2))
        return {"status": "saved", "path": str(dest), "total": len(self._state)}

    @route("api")
    def loadstate(self, path: str | None = None, skip_missing: bool = False) -> dict:
        """
        Rebuild registry from a JSON snapshot saved by ``savestate``.

        Args:
            path: Override state file path (default: configured state_path).
            skip_missing: If true, skip entries whose spec path is missing
                instead of failing the entire load.
        """
        source = self._resolve_state_path(path)
        if not source.exists():
            return {"error": "State file not found", "path": str(source)}

        try:
            payload = json.loads(source.read_text())
        except Exception as exc:
            return {"error": f"Invalid state file: {exc}", "path": str(source)}

        if isinstance(payload, dict) and "autosave" in payload:
            self._autosave = bool(payload.get("autosave"))

        result = self.app_manager.restore(payload, skip_missing=skip_missing)
        return {"status": "loaded", "path": str(source), **result}

    @route("api")
    def autosave(self, enabled: bool | None = None) -> dict:
        """
        Get or set autosave mode.

        Args:
            enabled: Optional flag to update autosave setting.
        """
        return self.app_manager.autosave(enabled)

    def _resolve_state_path(self, path: str | Path | None) -> Path:
        """Resolve a state file path relative to configured state_path."""
        return Path(path).expanduser().resolve() if path else self.state_path


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
    publisher.chan_registry.get("cli").run()


if __name__ == "__main__":
    main()
