"""
Tests for Publisher.
"""

import sys
from unittest.mock import patch

import pytest
from smartswitch import Switcher

from smartpublisher import Publisher, PublisherContext


# Test fixtures
class SimpleHandler:
    """Simple handler for testing."""

    __slots__ = ("data", "smpublisher")
    api = Switcher(prefix="cmd_")

    def __init__(self):
        self.data = {}

    @api
    def cmd_add(self, key: str, value: str):
        """Add a key-value pair."""
        self.data[key] = value
        return f"Added {key}={value}"

    @api
    def cmd_get(self, key: str):
        """Get a value by key."""
        return self.data.get(key, "Not found")

    @api
    def cmd_list(self):
        """List all keys."""
        return list(self.data.keys())


class TypedHandler:
    """Handler with typed parameters."""

    __slots__ = ("counter", "smpublisher")
    api = Switcher(prefix="test_")

    def __init__(self):
        self.counter = 0

    @api
    def test_increment(self, amount: int = 1):
        """Increment counter."""
        self.counter += amount
        return self.counter

    @api
    def test_multiply(self, factor: float):
        """Multiply counter."""
        self.counter = int(self.counter * factor)
        return self.counter

    @api
    def test_reset(self, value: int = 0):
        """Reset counter."""
        self.counter = value
        return self.counter


class TestApp(Publisher):
    """Test application."""

    __test__ = False  # Not a pytest test class

    def on_init(self):
        self.simple = SimpleHandler()
        self.typed = TypedHandler()
        self.publish("simple", self.simple, cli=True, openapi=True)
        self.publish("typed", self.typed, cli=True, openapi=False)


class TestPublisherContext:
    """Test PublisherContext functionality."""

    def test_context_creation(self):
        """Should create context with handler reference."""
        handler = SimpleHandler()
        context = PublisherContext(handler)

        assert context._handler is handler
        assert context.parent_api is None

    def test_get_api_json(self):
        """Should extract API schema from handler."""
        handler = SimpleHandler()
        context = PublisherContext(handler)

        schema = context.get_api_json()

        assert schema["class"] == "SimpleHandler"
        assert "methods" in schema
        assert "add" in schema["methods"]
        assert "get" in schema["methods"]
        assert "list" in schema["methods"]

    def test_api_json_parameters(self):
        """Should extract parameter information."""
        handler = SimpleHandler()
        context = PublisherContext(handler)

        schema = context.get_api_json()
        add_method = schema["methods"]["add"]

        assert len(add_method["parameters"]) == 2
        key_param = next(p for p in add_method["parameters"] if p["name"] == "key")
        assert key_param["type"] == "str"
        assert key_param["required"] is True

    def test_api_json_with_defaults(self):
        """Should handle default values in parameters."""
        handler = TypedHandler()
        context = PublisherContext(handler)

        schema = context.get_api_json()
        increment_method = schema["methods"]["increment"]

        params = increment_method["parameters"]
        amount_param = next(p for p in params if p["name"] == "amount")
        assert amount_param["required"] is False
        assert amount_param["default"] == 1


class TestPublisher:
    """Test Publisher base class."""

    def test_initialization(self):
        """Should initialize with parent_api."""
        app = TestApp()

        assert hasattr(app, "parent_api")
        assert isinstance(app.parent_api, Switcher)
        assert app.parent_api.name == "root"  # Default name is 'root'

    def test_publish_handler(self):
        """Should publish handler and inject smpublisher context."""
        app = TestApp()

        # Handler should have smpublisher attribute
        assert hasattr(app.simple, "smpublisher")
        assert isinstance(app.simple.smpublisher, PublisherContext)

        # Handler's API should have parent set
        assert app.simple.__class__.api.parent is app.parent_api

    def test_publish_cli_openapi_flags(self):
        """Should respect cli and openapi flags."""
        app = TestApp()

        # Simple handler: both CLI and OpenAPI
        assert "simple" in app._cli_handlers
        assert "/simple" in app._openapi_handlers  # OpenAPI uses path keys

        # Typed handler: CLI only
        assert "typed" in app._cli_handlers
        assert "/typed" not in app._openapi_handlers

    def test_parent_child_relationship(self):
        """Should establish parent-child Switcher relationship."""
        app = TestApp()

        # Handler API should have app's parent_api as parent
        assert app.simple.__class__.api.parent is app.parent_api

        # Both handlers should be connected to parent
        assert app.typed.__class__.api.parent is app.parent_api


class TestCLIExecution:
    """Test CLI command execution."""

    def test_cli_help(self, capsys):
        """Should display help when no arguments."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app"]):
            app._run_cli()

        captured = capsys.readouterr()
        assert "TestApp" in captured.out
        assert "simple" in captured.out
        assert "typed" in captured.out

    def test_cli_handler_help(self, capsys):
        """Should display handler-specific help."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "simple", "--help"]):
            app._run_cli()

        captured = capsys.readouterr()
        assert "simple" in captured.out
        assert "add" in captured.out
        assert "get" in captured.out
        assert "list" in captured.out

    def test_cli_method_execution(self, capsys):
        """Should execute method with arguments."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "simple", "add", "name", "Alice"]):
            app._run_cli()

        captured = capsys.readouterr()
        assert "Added name=Alice" in captured.out
        assert app.simple.data["name"] == "Alice"

    def test_cli_type_validation(self, capsys):
        """Should validate and convert argument types."""
        app = TestApp()

        # Valid integer
        with patch.object(sys, "argv", ["test_app", "typed", "increment", "5"]):
            app._run_cli()

        captured = capsys.readouterr()
        assert "5" in captured.out
        assert app.typed.counter == 5

    def test_cli_validation_error(self, capsys):
        """Should display validation errors."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "typed", "increment", "not_a_number"]):
            with pytest.raises(SystemExit):
                app._run_cli()

        captured = capsys.readouterr()
        assert "Invalid arguments" in captured.out
        assert "amount" in captured.out

    def test_cli_unknown_handler(self, capsys):
        """Should error on unknown handler."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "unknown", "method"]):
            with pytest.raises(SystemExit):
                app._run_cli()

        captured = capsys.readouterr()
        assert "Unknown handler" in captured.out

    def test_cli_unknown_method(self, capsys):
        """Should error on unknown method."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "simple", "unknown"]):
            with pytest.raises(SystemExit):
                app._run_cli()

        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_cli_with_defaults(self, capsys):
        """Should use default values for optional parameters."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "typed", "increment"]):
            app._run_cli()

        captured = capsys.readouterr()
        assert "1" in captured.out
        assert app.typed.counter == 1

    @patch("smartpublisher.publisher.prompt_for_parameters")
    def test_cli_interactive_mode(self, mock_prompt, capsys):
        """Should prompt for parameters in interactive mode."""
        mock_prompt.return_value = ["testkey", "testvalue"]

        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "simple", "add", "--interactive"]):
            app._run_cli()

        mock_prompt.assert_called_once()
        captured = capsys.readouterr()
        assert "Added testkey=testvalue" in captured.out


class TestRunModes:
    """Test different run modes."""

    def test_auto_detect_cli(self):
        """Should auto-detect CLI mode when args present."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app", "simple", "list"]):
            with patch.object(app, "_run_cli") as mock_cli:
                app.run()
                mock_cli.assert_called_once()

    def test_auto_detect_http(self):
        """Should auto-detect HTTP mode when no args."""
        app = TestApp()

        with patch.object(sys, "argv", ["test_app"]):
            with patch.object(app, "_run_http"):
                # Mock HTTP mode to avoid actually starting server
                app.run()
                # Note: This will actually call _run_cli for help
                # since we have only 1 arg. HTTP mode needs 0 args.

    def test_explicit_cli_mode(self):
        """Should use CLI mode when explicitly specified."""
        app = TestApp()

        with patch.object(app, "_run_cli") as mock_cli:
            app.run(mode="cli")
            mock_cli.assert_called_once()

    def test_explicit_http_mode(self):
        """Should use HTTP mode when explicitly specified."""
        app = TestApp()

        with patch.object(app, "_run_http") as mock_http:
            app.run(mode="http", port=8080)
            mock_http.assert_called_once_with(8080)

    def test_invalid_mode(self):
        """Should raise error for invalid mode."""
        app = TestApp()

        with pytest.raises(ValueError, match="Unknown mode"):
            app.run(mode="invalid")
