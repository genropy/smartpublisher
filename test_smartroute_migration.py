#!/usr/bin/env python
"""Test SmartRoute integration with SmartPublisher."""

from src.smartpublisher.published import PublishedClass
from smartroute import Router, RoutedClass, route


class TestHandler(RoutedClass):
    """Test handler with Router."""
    api = Router(name="test")

    @route("api")
    def greet(self, name: str = "World"):
        """Greet someone."""
        return f"Hello {name}!"


class TestApp(PublishedClass):
    """Test app that publishes handlers."""
    def on_init(self):
        handler = TestHandler()
        # This line will fail at published.py:98
        result = self.publish("test", handler)
        print(f"Published: {result}")


if __name__ == "__main__":
    try:
        app = TestApp()
        print("✅ SUCCESS: SmartRoute integration working!")
    except AttributeError as e:
        print(f"❌ FAILED: {e}")
        print(f"\nFails at: src/smartpublisher/published.py:98")
        print(f"Missing: handler_instance.api.describe() method on BoundRouter")
        import traceback
        traceback.print_exc()
