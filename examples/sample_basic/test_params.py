"""
Test handler to verify parameter display in help.
"""

import sys

sys.path.insert(0, "../../src")

from smartswitch import Switcher
from smpub import Publisher


class TestHandler:
    """Handler for testing parameter display."""

    api = Switcher(prefix="test_")

    def __init__(self):
        self.data = {}

    @api
    def test_simple(self, name: str):
        """Simple method with one required parameter."""
        return f"Hello {name}"

    @api
    def test_mixed(self, name: str, age: int = 25, active: bool = True):
        """Method with required and optional parameters."""
        return f"{name} is {age} years old, active={active}"

    @api
    def test_complex(
        self, host: str, port: int = 8080, timeout: float = 30.0, enabled: bool = True
    ):
        """Method with multiple types and defaults."""
        return f"Connecting to {host}:{port}"


class TestApp(Publisher):
    """Test application."""

    def initialize(self):
        self.handler = TestHandler()
        self.publish("test", self.handler)


if __name__ == "__main__":
    app = TestApp()
    app.run()
