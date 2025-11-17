"""
SmartPublisher - Framework for building CLI/API applications with SmartSwitch.

Key classes:
- PublishedClass: Mixin for user apps (inherit from this)
- Publisher: Central coordinator (ONE instance per system)
- AppRegistry: Registry for managing apps

Architecture:
- User apps inherit from PublishedClass
- Each app has its own root Switcher
- Publisher coordinates multiple apps and channels
- Channels (CLI, HTTP) expose apps via different transports
"""

from .published import PublishedClass
from .publisher import Publisher, get_publisher
from .registry import AppRegistry, get_local_registry, get_global_registry
from .system_commands import SystemCommands
from .output_formatter import OutputFormatter

__all__ = [
    'PublishedClass',
    'Publisher',
    'get_publisher',
    'AppRegistry',
    'get_local_registry',
    'get_global_registry',
    'SystemCommands',
    'OutputFormatter'
]
