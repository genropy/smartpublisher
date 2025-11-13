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
