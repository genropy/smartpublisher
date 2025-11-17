"""
Tests for interactive module (Textual-based parameter prompting).
"""

from unittest.mock import Mock, patch

import pytest

from smartpublisher.interactive import (
    is_textual_available,
    prompt_for_parameters,
)


class TestIsTextualAvailable:
    """Test textual availability detection."""

    def test_textual_available(self):
        """Should return True when textual is installed."""
        # If we're running tests, textual should be available
        assert is_textual_available() is True

    @patch("smartpublisher.interactive.App", None)
    def test_textual_not_available(self):
        """Should return False when textual is not imported."""
        from smartpublisher.interactive import is_textual_available as check

        assert check() is False


class TestPromptForParameters:
    """Test parameter prompting with Textual."""

    @patch("smartpublisher.interactive.is_textual_available", return_value=False)
    @patch("sys.exit", side_effect=SystemExit(1))
    def test_textual_not_available(self, mock_exit, mock_available):
        """Should exit when textual is not available."""

        def dummy_method(name: str):
            pass

        with pytest.raises(SystemExit):
            prompt_for_parameters(dummy_method)
        mock_exit.assert_called_once_with(1)

    @patch("smartpublisher.interactive.ParameterForm")
    @patch("smartpublisher.interactive.get_parameter_info")
    def test_no_parameters(self, mock_get_params, mock_form_class):
        """Should return empty list when no parameters."""
        # Mock get_parameter_info to return empty list
        mock_get_params.return_value = []

        def dummy_method():
            pass

        result = prompt_for_parameters(dummy_method)
        assert result == []
        # Form should not be created if no parameters
        mock_form_class.assert_not_called()

    @patch("smartpublisher.interactive.ParameterForm")
    @patch("smartpublisher.interactive.get_parameter_info")
    def test_prompt_all_parameters(self, mock_get_params, mock_form_class):
        """Should prompt for all parameters and return results."""
        # Mock parameter info
        params = [
            {"name": "name", "type": "str", "required": True, "default": None},
            {"name": "age", "type": "int", "required": True, "default": None},
            {"name": "active", "type": "bool", "required": True, "default": None},
        ]
        mock_get_params.return_value = params

        # Mock the form instance
        mock_form = Mock()
        mock_form.cancelled = False
        mock_form.values = {"name": "Alice", "age": "30", "active": True}
        mock_form.run = Mock()  # Mock the run method
        mock_form_class.return_value = mock_form

        def dummy_method(name: str, age: int, active: bool):
            pass

        result = prompt_for_parameters(dummy_method)
        assert result == ["Alice", "30", "True"]
        mock_form.run.assert_called_once()

    @patch("smartpublisher.interactive.ParameterForm")
    @patch("smartpublisher.interactive.get_parameter_info")
    def test_mixed_types(self, mock_get_params, mock_form_class):
        """Should handle mixed parameter types."""
        # Mock parameter info
        params = [
            {"name": "name", "type": "str", "required": True, "default": None},
            {"name": "count", "type": "int", "required": False, "default": "10"},
            {"name": "enabled", "type": "bool", "required": False, "default": "True"},
        ]
        mock_get_params.return_value = params

        # Mock the form instance
        mock_form = Mock()
        mock_form.cancelled = False
        mock_form.values = {"name": "Bob", "count": "42", "enabled": False}
        mock_form.run = Mock()  # Mock the run method
        mock_form_class.return_value = mock_form

        def dummy_method(name: str, count: int = 10, enabled: bool = True):
            pass

        result = prompt_for_parameters(dummy_method)
        assert result == ["Bob", "42", "False"]

    @patch("smartpublisher.interactive.ParameterForm")
    @patch("smartpublisher.interactive.get_parameter_info")
    def test_optional_parameters_with_defaults(self, mock_get_params, mock_form_class):
        """Should handle optional parameters with default values."""
        # Mock parameter info
        params = [
            {"name": "name", "type": "str", "required": True, "default": None},
            {"name": "port", "type": "int", "required": False, "default": "8080"},
        ]
        mock_get_params.return_value = params

        # Mock the form instance with empty value for port (use default)
        mock_form = Mock()
        mock_form.cancelled = False
        mock_form.values = {"name": "Charlie", "port": ""}  # Empty, should use default
        mock_form.run = Mock()  # Mock the run method
        mock_form_class.return_value = mock_form

        def dummy_method(name: str, port: int = 8080):
            pass

        result = prompt_for_parameters(dummy_method)
        assert result == ["Charlie", "8080"]

    @patch("smartpublisher.interactive.ParameterForm")
    @patch("smartpublisher.interactive.get_parameter_info")
    @patch("sys.exit", side_effect=SystemExit(0))
    def test_cancelled(self, mock_exit, mock_get_params, mock_form_class):
        """Should exit when user cancels."""
        # Mock parameter info
        params = [{"name": "name", "type": "str", "required": True, "default": None}]
        mock_get_params.return_value = params

        # Mock the form instance as cancelled
        mock_form = Mock()
        mock_form.cancelled = True
        mock_form.values = {}
        mock_form.run = Mock()  # Mock the run method
        mock_form_class.return_value = mock_form

        def dummy_method(name: str):
            pass

        with pytest.raises(SystemExit):
            prompt_for_parameters(dummy_method)
        mock_exit.assert_called_once_with(0)


# Additional tests using textual.testing for real TUI testing
try:
    from textual.testing import AppTest
    from smartpublisher.interactive import ParameterForm

    TEXTUAL_TESTING_AVAILABLE = True
except ImportError:
    TEXTUAL_TESTING_AVAILABLE = False


@pytest.mark.skipif(not TEXTUAL_TESTING_AVAILABLE, reason="Textual testing not available")
class TestParameterFormTUI:
    """Test ParameterForm TUI with real textual.testing."""

    async def test_form_renders_with_string_parameter(self):
        """Should render form with string input field."""
        params = [{"name": "username", "type": "str", "required": True, "default": None}]

        app = ParameterForm(params)
        async with app.run_test():
            # Check that input field exists
            assert app.query_one("#field_username") is not None

    async def test_form_renders_with_default_value(self):
        """Should populate input with default value."""
        params = [{"name": "port", "type": "int", "required": False, "default": 8000}]

        app = ParameterForm(params)
        async with app.run_test():
            input_field = app.query_one("#field_port")
            assert input_field.value == "8000"

    async def test_form_renders_boolean_as_switch(self):
        """Should render Switch widget for boolean parameters."""
        params = [{"name": "enabled", "type": "bool", "required": False, "default": True}]

        app = ParameterForm(params)
        async with app.run_test():
            from textual.widgets import Switch

            switch = app.query_one("#field_enabled")
            assert isinstance(switch, Switch)
            assert switch.value is True

    async def test_form_renders_literal_as_radioset(self):
        """Should render RadioSet for Literal types."""
        params = [
            {
                "name": "level",
                "type": "Literal['debug', 'info', 'error']",
                "required": False,
                "default": "info",
            }
        ]

        app = ParameterForm(params)
        async with app.run_test():
            from textual.widgets import RadioSet

            radioset = app.query_one("#field_level")
            assert isinstance(radioset, RadioSet)

    async def test_submit_button_collects_string_values(self):
        """Should collect string values when submit is clicked."""
        params = [
            {"name": "name", "type": "str", "required": True, "default": None},
            {"name": "email", "type": "str", "required": False, "default": ""},
        ]

        app = ParameterForm(params)
        async with app.run_test() as pilot:
            # Fill in name field
            name_input = app.query_one("#field_name")
            name_input.value = "Alice"

            # Fill in email field
            email_input = app.query_one("#field_email")
            email_input.value = "alice@example.com"

            # Click submit
            await pilot.click("#submit")

            # Check values were collected
            assert app.values["name"] == "Alice"
            assert app.values["email"] == "alice@example.com"

    async def test_submit_button_collects_boolean_values(self):
        """Should collect boolean values from Switch widgets."""
        params = [{"name": "debug", "type": "bool", "required": False, "default": False}]

        app = ParameterForm(params)
        async with app.run_test() as pilot:
            # Toggle switch
            app.query_one("#field_debug")
            await pilot.click("#field_debug")

            # Submit
            await pilot.click("#submit")

            # Check boolean was collected
            assert app.values["debug"] is True

    async def test_cancel_button_sets_cancelled_flag(self):
        """Should set cancelled flag when cancel is clicked."""
        params = [{"name": "test", "type": "str", "required": True, "default": None}]

        app = ParameterForm(params)
        async with app.run_test() as pilot:
            await pilot.click("#cancel")
            assert app.cancelled is True

    async def test_escape_key_cancels_form(self):
        """Should cancel form when Escape key is pressed."""
        params = [{"name": "test", "type": "str", "required": True, "default": None}]

        app = ParameterForm(params)
        async with app.run_test() as pilot:
            await pilot.press("escape")
            assert app.cancelled is True

    async def test_form_with_multiple_parameter_types(self):
        """Should render form with multiple different parameter types."""
        params = [
            {"name": "name", "type": "str", "required": True, "default": None},
            {"name": "port", "type": "int", "required": False, "default": 8000},
            {"name": "debug", "type": "bool", "required": False, "default": False},
        ]

        app = ParameterForm(params)
        async with app.run_test():
            # All fields should exist
            assert app.query_one("#field_name") is not None
            assert app.query_one("#field_port") is not None
            assert app.query_one("#field_debug") is not None

            # Buttons should exist
            assert app.query_one("#submit") is not None
            assert app.query_one("#cancel") is not None

    async def test_submit_with_empty_optional_field_uses_default(self):
        """Should handle empty optional fields correctly."""
        params = [
            {"name": "required", "type": "str", "required": True, "default": None},
            {"name": "optional", "type": "int", "required": False, "default": 42},
        ]

        app = ParameterForm(params)
        async with app.run_test() as pilot:
            # Fill only required field
            required_input = app.query_one("#field_required")
            required_input.value = "test"

            # Leave optional field with default
            optional_input = app.query_one("#field_optional")
            assert optional_input.value == "42"

            # Submit
            await pilot.click("#submit")

            assert app.values["required"] == "test"
            assert app.values["optional"] == "42"

    async def test_radioset_collects_selected_value(self):
        """Should collect selected radio button value."""
        params = [
            {
                "name": "choice",
                "type": "Literal['a', 'b', 'c']",
                "required": False,
                "default": "b",
            }
        ]

        app = ParameterForm(params)
        async with app.run_test() as pilot:
            # RadioSet should have 'b' selected by default
            app.query_one("#field_choice")

            # Submit without changing
            await pilot.click("#submit")

            # Should collect the default value
            assert "choice" in app.values

    async def test_form_title(self):
        """Should have correct title."""
        params = [{"name": "test", "type": "str", "required": True, "default": None}]

        app = ParameterForm(params)
        assert app.title == "Parameter Input"

    async def test_form_help_text_visible(self):
        """Should display help text about Tab navigation."""
        params = [{"name": "test", "type": "str", "required": True, "default": None}]

        app = ParameterForm(params)
        async with app.run_test():
            # Check that help label exists
            help_label = app.query_one(".help")
            assert help_label is not None
            assert "Tab" in help_label.renderable or "tab" in str(help_label.renderable).lower()

    async def test_required_field_placeholder(self):
        """Should show 'Required' placeholder for required fields."""
        params = [{"name": "test", "type": "str", "required": True, "default": None}]

        app = ParameterForm(params)
        async with app.run_test():
            input_field = app.query_one("#field_test")
            assert input_field.placeholder == "Required"

    async def test_optional_field_placeholder(self):
        """Should show 'Optional' placeholder for optional fields."""
        params = [{"name": "test", "type": "str", "required": False, "default": None}]

        app = ParameterForm(params)
        async with app.run_test():
            input_field = app.query_one("#field_test")
            assert input_field.placeholder == "Optional"
