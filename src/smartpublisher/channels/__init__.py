"""
Channel implementations for SmartPublisher.

Each channel is a separate class with its own Switcher for channel-specific commands.
"""

from .cli import PublisherCLI
from .http import PublisherHTTP

__all__ = ['PublisherCLI', 'PublisherHTTP']
