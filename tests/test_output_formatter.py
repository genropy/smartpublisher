"""Tests for output formatter."""

from smartpublisher.output_formatter import OutputFormatter


class TestOutputFormatter:
    """Test OutputFormatter functionality."""

    def test_format_json_pretty(self):
        """Should format JSON with pretty printing."""
        data = {"key": "value", "number": 42}
        result = OutputFormatter.format_json(data, pretty=True)

        assert isinstance(result, str)
        assert '"key"' in result
        assert '"value"' in result
        assert "42" in result
        # Pretty formatting adds newlines
        assert "\n" in result

    def test_format_json_compact(self):
        """Should format JSON compactly."""
        data = {"key": "value"}
        result = OutputFormatter.format_json(data, pretty=False)

        assert isinstance(result, str)
        assert '"key"' in result
        # Compact should not have indentation newlines
        assert result.count("\n") == 0

    def test_format_json_list(self):
        """Should format list as JSON."""
        data = ["item1", "item2", "item3"]
        result = OutputFormatter.format_json(data)

        assert isinstance(result, str)
        assert "item1" in result
        assert "item2" in result

    def test_format_json_nested(self):
        """Should format nested structures."""
        data = {"app": "test", "handlers": ["h1", "h2"], "config": {"key": "value"}}
        result = OutputFormatter.format_json(data)

        assert isinstance(result, str)
        assert "app" in result
        assert "handlers" in result

    def test_format_table_with_handlers(self):
        """Should format handler list as table."""
        data = {
            "handlers": {
                "test": {"class": "TestHandler", "methods": ["greet", "farewell"]},
                "admin": {"class": "AdminHandler", "methods": ["login"]},
            }
        }
        result = OutputFormatter.format_table(data)

        assert isinstance(result, str)
        assert "Handlers:" in result
        assert "test" in result
        assert "TestHandler" in result
        assert "greet" in result

    def test_format_table_generic_dict(self):
        """Should format generic dict as JSON."""
        data = {"status": "ok", "count": 5}
        result = OutputFormatter.format_table(data)

        assert isinstance(result, str)
        assert "status" in result

    def test_format_table_non_dict(self):
        """Should handle non-dict input."""
        data = "simple string"
        result = OutputFormatter.format_table(data)

        assert isinstance(result, str)
        assert data in result

    def test_format_error_with_dict(self):
        """Should format error dictionary."""
        error_data = {"error": "Handler not found", "available": ["h1", "h2"]}
        result = OutputFormatter.format_error(error_data)

        assert isinstance(result, str)
        assert "Error:" in result
        assert "Handler not found" in result
        assert "Available:" in result

    def test_format_error_simple(self):
        """Should handle simple error data."""
        error_data = {"error": "Something went wrong"}
        result = OutputFormatter.format_error(error_data)

        assert isinstance(result, str)
        assert "Error:" in result
        assert "Something went wrong" in result

    def test_format_error_non_dict(self):
        """Should handle non-dict error."""
        error_data = "Error message"
        result = OutputFormatter.format_error(error_data)

        assert isinstance(result, str)
        assert error_data in result

    def test_format_help(self):
        """Should format help from API schema."""
        api_schema = {
            "methods": {
                "greet": {
                    "description": "Greet someone",
                    "parameters": [{"name": "name", "type": "str", "required": True}],
                },
                "farewell": {
                    "description": "Say goodbye",
                    "parameters": [
                        {"name": "name", "type": "str", "required": False, "default": "World"}
                    ],
                },
            }
        }
        result = OutputFormatter.format_help(api_schema)

        assert isinstance(result, str)
        assert "Available commands:" in result
        assert "greet" in result
        assert "farewell" in result
        assert "Greet someone" in result

    def test_format_help_empty_schema(self):
        """Should handle empty API schema."""
        api_schema = {}
        result = OutputFormatter.format_help(api_schema)

        assert isinstance(result, str)
