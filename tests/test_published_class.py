"""Tests for PublishedClass with SmartRoute integration."""

from smartroute import Router, RoutedClass, route

from smartpublisher.published import PublishedClass


class TestPublishedClass:
    """Test PublishedClass basic functionality."""

    def test_init(self):
        """Should initialize PublishedClass with Router."""

        class MyApp(PublishedClass):
            pass

        app = MyApp()

        # Should have api router
        assert hasattr(app, 'api')

        # Should have _system auto-published
        assert '_system' in app.list_handlers()

        # Should have _publisher reference (None initially)
        assert app._publisher is None

    def test_publish_handler(self):
        """Should publish a handler and extract methods."""

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
                self.result = self.publish("test", handler)

        app = TestApp()

        # Check publish result
        assert app.result["status"] == "published"
        assert app.result["name"] == "test"
        assert app.result["handler_class"] == "TestHandler"
        assert "greet" in app.result["methods"]

        # Check handler is tracked
        assert "test" in app.list_handlers()
        assert isinstance(app.get_handler("test"), TestHandler)

    def test_publish_multiple_handlers(self):
        """Should publish multiple handlers."""

        class Handler1(RoutedClass):
            api = Router(name="h1")

            @route("api")
            def method1(self):
                """Method 1."""
                return "h1"

        class Handler2(RoutedClass):
            api = Router(name="h2")

            @route("api")
            def method2(self):
                """Method 2."""
                return "h2"

        class TestApp(PublishedClass):
            def on_init(self):
                self.publish("h1", Handler1())
                self.publish("h2", Handler2())

        app = TestApp()

        # Both handlers should be tracked
        assert set(app.list_handlers()) == {"_system", "h1", "h2"}
        assert isinstance(app.get_handler("h1"), Handler1)
        assert isinstance(app.get_handler("h2"), Handler2)

    def test_publish_handler_without_router(self):
        """Should handle publishing handler without router."""

        class PlainHandler:
            """Handler without Router."""
            def some_method(self):
                return "plain"

        class TestApp(PublishedClass):
            def on_init(self):
                handler = PlainHandler()
                self.result = self.publish("plain", handler)

        app = TestApp()

        # Should still work but with empty methods
        assert app.result["status"] == "published"
        assert app.result["methods"] == []

    def test_router_hierarchy(self):
        """Should create hierarchical router structure."""

        class ChildHandler(RoutedClass):
            api = Router(name="child")

            @route("api")
            def child_method(self):
                """Child method."""
                return "child"

        class ParentApp(PublishedClass):
            def on_init(self):
                self.publish("child", ChildHandler())

        app = ParentApp()

        # Should be able to access child via parent's api
        # This tests the add_child() integration
        result = app.api.get("child.child_method")()
        assert result == "child"

    def test_lifecycle_hooks(self):
        """Should call lifecycle hooks."""

        class TestApp(PublishedClass):
            def __init__(self):
                self.init_called = False
                super().__init__()

            def on_init(self):
                self.init_called = True

        app = TestApp()

        # on_init should have been called
        assert app.init_called is True

    def test_system_commands_published(self):
        """Should automatically publish system commands."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()

        # _system handler should be auto-published
        assert app.get_handler("_system") is not None

    def test_set_publisher_reference(self):
        """Should allow setting publisher reference."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()

        # Mock publisher
        mock_publisher = object()

        app._set_publisher(mock_publisher)

        assert app._publisher is mock_publisher

    def test_smpub_on_add_hook(self):
        """Should return registration info on add."""

        class TestApp(PublishedClass):
            def on_init(self):
                self.publish("handler", RoutedClass())

        app = TestApp()

        result = app.smpub_on_add()

        assert "message" in result
        assert "handlers" in result
        assert "handler" in result["handlers"]

    def test_smpub_on_remove_hook(self):
        """Should return cleanup info on remove."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()

        result = app.smpub_on_remove()

        assert "message" in result
        assert "TestApp" in result["message"]
