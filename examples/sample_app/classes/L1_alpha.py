"""
L1_alpha - Level 1 Alpha handler.
"""

from smartswitch import Switcher
from .L2_alpha_s1 import L2_alpha_s1


class L1_alpha:
    """Level 1 - Alpha class."""

    api = Switcher(prefix="alpha_")

    def __init__(self):
        self.registry = {}

    @api
    def alpha_add(self, key):
        """Add a new L2_alpha_s1 instance to the registry."""
        instance = L2_alpha_s1()
        self.registry[key] = instance
        return instance

    @api
    def alpha_del(self, key):
        """Remove an instance from the registry."""
        if key in self.registry:
            del self.registry[key]
            return True
        return False

    @api
    def alpha_list(self):
        """List all registered instances."""
        return list(self.registry.keys())
