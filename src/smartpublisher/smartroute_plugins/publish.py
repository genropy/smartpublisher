"""Attach scope/channel policy for apps ready to publish.

Public API exported
-------------------
- class ``PublishPlugin``: SmartRoute plugin that annotates handlers with
  scope tags and allowed channels.
- constant ``STANDARD_CHANNELS``: reference channel codes.

External dependencies
---------------------
- ``smartroute`` core ``Router`` plus ``BasePlugin``/``MethodEntry`` for plugin
  lifecycle.
- ``fnmatchcase`` for wildcard scope matching.

Invariants and limitations
--------------------------
- Accepts only uppercase channel codes; normalization errors raise
  ``ValueError``/``TypeError``.
- Stores copies of provided configs to avoid shared mutation.
- Applies scope metadata only when tags are present; otherwise removes it.
- Pattern matching uses ``fnmatchcase``; wildcard channels use ``*`` key.

Side effects
------------
- Registers itself as ``publish`` plugin on ``Router`` at import time.

Extension points
----------------
- Override ``DEFAULT_SCOPE_RULES`` in subclasses for different defaults.
- Extend ``STANDARD_CHANNELS`` upstream if new publisher channels are added.
- Convention proposal: each channel module exposes ``CHANNEL_CODES`` as a map
  ``{CODE: "Description"}``; the plugin can enrich available channels with it.
  Today this is static (future implementation).

Minimal usage
-------------
```
from smartpublisher.smartroute_plugins.publish import PublishPlugin

router = Router(name="app").plug(PublishPlugin())
@router.route("api", metadata={"scopes": "public", "scope_channels": {"public": ["HTTP"]}})
def hello(): ...
```"""

from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Any, Dict, Iterable, List, Optional

from smartroute.core.router import Router
from smartroute.plugins._base_plugin import BasePlugin, MethodEntry

STANDARD_CHANNELS = {
    "CLI": "Publisher CLI commands",
    "SYS_HTTP": "Shared Publisher HTTP API",
    "SYS_WS": "Shared Publisher WebSocket API",
    "HTTP": "Application HTTP API",
    "WS": "Application WebSocket API",
    "MCP": "Machine Control Protocol / AI adapter",
}

__all__ = ["PublishPlugin", "STANDARD_CHANNELS"]


class PublishPlugin(BasePlugin):
    """Attach scope metadata to handlers and resolve allowed channels."""

    DEFAULT_SCOPE_RULES = [
        ("internal", ["CLI", "SYS_HTTP"]),
        ("public", ["HTTP"]),
        ("public_*", ["HTTP"]),
    ]

    def __init__(self, name: Optional[str] = None, **config: Any):
        config = dict(config)
        self._promote_channel_alias(config)
        super().__init__(name=name or "publish", **config)
        self._router: Optional[Router] = None
        self._entries: Dict[str, MethodEntry] = {}
        self._entry_overrides: Dict[str, Dict[str, Any]] = {}
        self._channel_catalog = dict(STANDARD_CHANNELS)

    # ------------------------------------------------------------------
    # Plugin lifecycle
    # ------------------------------------------------------------------
    def on_decore(self, router: Router, func, entry: MethodEntry) -> None:
        """Capture entry metadata and attach scope payload."""
        self._router = router
        self._refresh_channel_catalog(router)
        self._entries[entry.name] = entry
        stored = self._entry_overrides.setdefault(entry.name, {})
        if "scopes" not in stored:
            stored["scopes"] = self._normalize_scopes(entry.metadata.get("scopes"))
        if "scope_channels" not in stored:
            stored["scope_channels"] = self._normalize_scope_channels(
                entry.metadata.get("scope_channels")
            )
        self._apply_scope_metadata(entry)

    def set_config(self, flags: Optional[str] = None, **config: Any) -> None:
        """Update global config and refresh scope metadata."""
        config = dict(config)
        self._promote_channel_alias(config)
        super().set_config(flags=flags, **config)
        self._refresh_entries()

    def set_method_config(
        self, method_name: str, *, flags: Optional[str] = None, **config: Any
    ) -> None:
        """Update per-method config and refresh scope metadata."""
        config = dict(config)
        self._promote_channel_alias(config)
        super().set_method_config(method_name, flags=flags, **config)
        self._refresh_entries(method_name)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def describe_method(self, method_name: str) -> Optional[Dict[str, Any]]:
        payload = self._build_scope_payload(method_name)
        if not payload or not payload.get("tags"):
            return None  # absence path
        return payload

    def describe_entry(
        self, router: Router, entry: MethodEntry, base_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expose scope metadata for describe() hook."""
        payload = self.describe_method(entry.name)
        return {"scope": payload} if payload else {}

    def describe_scopes(self) -> Dict[str, Dict[str, Any]]:
        """Return scope payload for every known entry."""
        info: Dict[str, Dict[str, Any]] = {}
        for method_name in self._entries.keys():
            payload = self.describe_method(method_name)
            if payload:
                info[method_name] = payload
        return info

    def get_channel_map(self, channel: str) -> Dict[str, Dict[str, Any]]:
        """Return handlers whose scopes are exposed on the given channel."""
        target = self._validate_channel_code(channel)
        if not target:
            raise ValueError("Channel code cannot be empty")
        matrix: Dict[str, Dict[str, Any]] = {}
        for method_name, payload in self.describe_scopes().items():
            scoped_channels = payload.get("channels", {})
            matching = [scope for scope, channels in scoped_channels.items() if target in channels]
            if matching:
                matrix[method_name] = {
                    "tags": payload["tags"],
                    "channels": scoped_channels,
                    "exposed_scopes": matching,
                }
        return matrix

    def filter_entry(self, router: Router, entry: MethodEntry, **filters: Any) -> bool:
        """Filter entries by scope/channel metadata."""
        scope_filter = filters.get("scopes")
        channel_filter = filters.get("channel")
        if not scope_filter and not channel_filter:
            return True
        scope_meta = entry.metadata.get("scope") if entry.metadata else None
        tags = scope_meta.get("tags") if isinstance(scope_meta, dict) else None
        if scope_filter:
            if not tags or not any(tag in scope_filter for tag in tags):
                return False
        if channel_filter:
            # If no scope/channel metadata, consider it allowed (no restriction set)
            if not scope_meta:
                return True
            channel_map = scope_meta.get("channels", {}) if isinstance(scope_meta, dict) else {}
            if not isinstance(channel_map, dict):
                return False
            if not channel_map:
                return True
            relevant_scopes = tags or list(channel_map.keys())
            allowed: set[str] = set()
            for scope_name in relevant_scopes:
                codes = channel_map.get(scope_name, [])
                for code in codes or []:
                    normalized = str(code).strip()
                    if normalized:
                        allowed.add(normalized)
            if not allowed:
                return True
            if channel_filter not in allowed:
                return False
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _refresh_entries(self, method_name: Optional[str] = None) -> None:
        if method_name:
            entry = self._entries.get(method_name)
            if entry:
                self._apply_scope_metadata(entry)
            return
        for entry in self._entries.values():
            self._apply_scope_metadata(entry)

    def _apply_scope_metadata(self, entry: MethodEntry) -> None:
        payload = self._build_scope_payload(entry.name)
        if payload and payload.get("tags"):
            entry.metadata["scope"] = payload
        else:
            entry.metadata.pop("scope", None)

    def _build_scope_payload(self, method_name: str) -> Optional[Dict[str, Any]]:
        scopes = self._resolve_scopes(method_name)
        if not scopes:
            return None
        channels = self._resolve_channels(method_name, scopes)
        return {"tags": scopes, "channels": channels}

    def _resolve_scopes(self, method_name: str) -> List[str]:
        method_cfg = self._handler_configs.get(method_name, {})
        if "scopes" in method_cfg:
            return self._normalize_scopes(method_cfg.get("scopes"))

        metadata_scopes = self._entry_overrides.get(method_name, {}).get("scopes") or []
        if metadata_scopes:
            return list(metadata_scopes)

        return self._normalize_scopes(self._global_config.get("scopes"))

    def _resolve_channels(self, method_name: str, scopes: Iterable[str]) -> Dict[str, List[str]]:
        global_map = self._normalize_scope_channels(self._global_config.get("scope_channels"))
        metadata_map = self._entry_overrides.get(method_name, {}).get("scope_channels") or {}
        method_map = self._normalize_scope_channels(
            self._handler_configs.get(method_name, {}).get("scope_channels")
        )

        merged = self._merge_channel_maps(global_map, metadata_map)
        merged = self._merge_channel_maps(merged, method_map)

        return {scope: self._resolve_channels_for_scope(scope, merged) for scope in scopes}

    def _resolve_channels_for_scope(self, scope: str, mapping: Dict[str, List[str]]) -> List[str]:
        channels = self._match_channel_entry(scope, mapping)
        if channels:
            return channels
        return self._default_channels_for_scope(scope)

    def _match_channel_entry(self, scope: str, mapping: Dict[str, List[str]]) -> List[str]:
        if scope in mapping:
            return list(mapping[scope])
        matched_pattern = self._match_pattern(scope, mapping)
        if matched_pattern is not None:
            return list(matched_pattern)
        fallback = mapping.get("*")
        if fallback:
            return list(fallback)
        return []

    def _match_pattern(self, scope: str, mapping: Dict[str, List[str]]) -> Optional[List[str]]:
        for key, channels in mapping.items():
            if key in {scope, "*"}:
                continue
            if any(token in key for token in "*?[]") and fnmatchcase(scope, key):
                return list(channels)
        return None

    def _merge_channel_maps(
        self, base: Dict[str, List[str]], extra: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        if not extra:
            return dict(base)
        merged = dict(base)
        for key, channels in extra.items():
            merged[key] = self._normalize_channel_list(channels)
        return merged

    def _refresh_channel_catalog(self, router: Router) -> None:
        """Import channel codes from a publisher-owned ChanRegistry if present."""
        publisher = getattr(router, "_instance", None)
        chan_registry = getattr(publisher, "chan_registry", None)
        if chan_registry and hasattr(chan_registry, "channel_codes"):
            codes = getattr(chan_registry, "channel_codes", {}) or {}
            if isinstance(codes, dict):
                for code, desc in codes.items():
                    if code and code not in self._channel_catalog:
                        self._channel_catalog[str(code)] = str(desc)

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------
    def _promote_channel_alias(self, config: Dict[str, Any]) -> None:
        if "channels" not in config:
            return
        channels = self._normalize_channel_list(config.pop("channels"))
        scope_map = config.setdefault("scope_channels", {})
        if not isinstance(scope_map, dict):
            raise TypeError("scope_channels must be a dict")
        existing_raw = scope_map.get("*") or []
        existing = (
            list(existing_raw)
            if isinstance(existing_raw, list)
            else self._normalize_channel_list(existing_raw)
        )
        merged = list(existing) + [c for c in channels if c not in existing]
        scope_map["*"] = merged

    def _normalize_scopes(self, raw) -> List[str]:
        if not raw:
            return []
        if isinstance(raw, str):
            tokens = [token.strip() for token in raw.split(",")]
        elif isinstance(raw, Iterable):
            tokens = []
            for item in raw:
                if not item:
                    continue
                tokens.append(str(item).strip())
        else:
            raise TypeError("scopes must be a string or iterable of strings")
        cleaned: List[str] = []
        for token in tokens:
            if not token or token in cleaned:
                continue
            cleaned.append(token)
        return cleaned

    def _normalize_scope_channels(self, raw) -> Dict[str, List[str]]:
        if not raw:
            return {}
        if not isinstance(raw, dict):
            raise TypeError("scope_channels must be a dict of scope -> channels")
        normalized: Dict[str, List[str]] = {}
        for scope, channels in raw.items():
            if not scope:
                raise ValueError("Scope name cannot be empty in scope_channels")
            normalized[str(scope)] = self._normalize_channel_list(channels)
        return normalized

    def _normalize_channel_list(self, raw) -> List[str]:
        if not raw:
            return []
        if isinstance(raw, str):
            tokens = [chunk.strip() for chunk in raw.split(",")]
        elif isinstance(raw, Iterable):
            tokens = []
            for item in raw:
                if not item:
                    continue
                tokens.append(str(item).strip())
        else:
            raise TypeError("Channels must be provided as string or iterable")
        cleaned: List[str] = []
        for token in tokens:
            normalized = self._validate_channel_code(token)
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned

    def _validate_channel_code(self, code: str) -> str:
        normalized = (code or "").strip()
        if not normalized:
            return ""
        if normalized != normalized.upper():
            raise ValueError(f"Channel code '{normalized}' must be uppercase (e.g. CLI, SYS_HTTP)")
        return normalized

    def _default_channels_for_scope(self, scope: str) -> List[str]:
        scope_name = (scope or "").strip()
        for pattern, channels in self.DEFAULT_SCOPE_RULES:
            if pattern == scope_name or fnmatchcase(scope_name, pattern):
                return [self._validate_channel_code(code) for code in channels]
        return []

    def available_channels(self) -> Dict[str, str]:
        """
        Return known channel codes with descriptions.

        Combines static STANDARD_CHANNELS with any CHANNEL_CODES exposed by
        registered channel classes (if the router belongs to a Publisher).
        """
        return dict(self._channel_catalog)


Router.register_plugin("publish", PublishPlugin)
