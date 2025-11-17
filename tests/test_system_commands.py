"""Tests for system commands."""

from smartroute import Router, RoutedClass, route
from smartroute.core.router import BoundRouter

from smartpublisher.system_commands import SystemCommands
from smartpublisher.published import PublishedClass


class TestSystemCommands:
    """Test SystemCommands functionality."""

    def test_init(self):
        """Should initialize with publisher instance."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        assert sys_commands.publisher is app

    def test_has_api_router(self):
        """Should have api Router."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        assert hasattr(sys_commands, 'api')
        # Instance access to Router returns BoundRouter
        assert isinstance(sys_commands.api, BoundRouter)

    def test_list_handlers_method_exists(self):
        """Should have list_handlers method."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        assert hasattr(sys_commands, 'list_handlers')
        assert callable(sys_commands.list_handlers)

    def test_list_handlers(self):
        """Should list all published handlers."""

        class TestHandler(RoutedClass):
            api = Router(name="test")

            @route("api")
            def greet(self):
                return "hello"

        class TestApp(PublishedClass):
            def on_init(self):
                self.publish("test", TestHandler())

        app = TestApp()
        sys_commands = SystemCommands(app)

        result = sys_commands.list_handlers()

        assert "handlers" in result
        assert "test" in result["handlers"]
        assert result["handlers"]["test"]["class"] == "TestHandler"

    def test_get_handler_info_method_exists(self):
        """Should have get_handler_info method."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        assert hasattr(sys_commands, 'get_handler_info')
        assert callable(sys_commands.get_handler_info)

    def test_get_handler_info(self):
        """Should get detailed handler info."""

        class TestHandler(RoutedClass):
            """Test handler docstring."""
            api = Router(name="test")

            @route("api")
            def greet(self):
                return "hello"

        class TestApp(PublishedClass):
            def on_init(self):
                self.publish("test", TestHandler())

        app = TestApp()
        sys_commands = SystemCommands(app)

        result = sys_commands.get_handler_info("test")

        assert result["name"] == "test"
        assert result["class"] == "TestHandler"
        assert "Test handler docstring" in result["docstring"]

    def test_get_handler_info_not_found(self):
        """Should return error for nonexistent handler."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        result = sys_commands.get_handler_info("nonexistent")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_get_api_tree_method_exists(self):
        """Should have get_api_tree method."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        assert hasattr(sys_commands, 'get_api_tree')
        assert callable(sys_commands.get_api_tree)

    def test_get_api_tree(self):
        """Should return complete API tree."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()
        sys_commands = SystemCommands(app)

        result = sys_commands.get_api_tree()

        # Should return describe() output from publisher's api
        assert isinstance(result, dict)

    def test_integrated_with_published_class(self):
        """Should be auto-integrated with PublishedClass."""

        class TestApp(PublishedClass):
            pass

        app = TestApp()

        # _system should be auto-published
        assert '_system' in app.published_instances
        assert isinstance(app.published_instances['_system'], SystemCommands)
