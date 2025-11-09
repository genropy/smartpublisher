"""
Tests for interactive module (gum-based parameter prompting).
"""

import subprocess
from unittest.mock import Mock, patch, call

import pytest

from smpub.interactive import (
    is_gum_available,
    prompt_for_parameter,
    prompt_for_boolean,
    prompt_for_parameters,
)


class TestIsGumAvailable:
    """Test gum availability detection."""

    @patch('subprocess.run')
    def test_gum_available(self, mock_run):
        """Should return True when gum is installed."""
        mock_run.return_value = Mock(returncode=0)

        assert is_gum_available() is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ['gum', '--version']

    @patch('subprocess.run')
    def test_gum_not_found(self, mock_run):
        """Should return False when gum is not in PATH."""
        mock_run.side_effect = FileNotFoundError()

        assert is_gum_available() is False

    @patch('subprocess.run')
    def test_gum_error(self, mock_run):
        """Should return False when gum command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gum')

        assert is_gum_available() is False


class TestPromptForParameter:
    """Test single parameter prompting."""

    @patch('subprocess.run')
    def test_prompt_required_parameter(self, mock_run):
        """Should prompt for required parameter."""
        mock_run.return_value = Mock(stdout="Alice\n", returncode=0)

        param_info = {
            'name': 'username',
            'type': 'str',
            'required': True,
            'default': None
        }

        result = prompt_for_parameter(param_info)
        assert result == "Alice"

        # Check gum was called correctly
        call_args = mock_run.call_args
        assert 'gum' in call_args[0][0]
        assert 'input' in call_args[0][0]

    @patch('subprocess.run')
    def test_prompt_optional_parameter(self, mock_run):
        """Should show default for optional parameter."""
        mock_run.return_value = Mock(stdout="30\n", returncode=0)

        param_info = {
            'name': 'age',
            'type': 'int',
            'required': False,
            'default': 25
        }

        result = prompt_for_parameter(param_info)
        assert result == "30"

        # Check that default value was passed to gum
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert '--value' in cmd
        assert '25' in cmd

    @patch('subprocess.run')
    def test_prompt_empty_with_default(self, mock_run):
        """Should use default when user provides empty input."""
        mock_run.return_value = Mock(stdout="\n", returncode=0)

        param_info = {
            'name': 'port',
            'type': 'int',
            'required': False,
            'default': 8080
        }

        result = prompt_for_parameter(param_info)
        assert result == "8080"

    @patch('subprocess.run')
    @patch('sys.exit')
    def test_prompt_cancelled(self, mock_exit, mock_run):
        """Should exit gracefully when user cancels."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gum')

        param_info = {
            'name': 'test',
            'type': 'str',
            'required': True,
            'default': None
        }

        prompt_for_parameter(param_info)
        mock_exit.assert_called_once_with(0)


class TestPromptForBoolean:
    """Test boolean parameter prompting."""

    @patch('subprocess.run')
    def test_prompt_boolean_true(self, mock_run):
        """Should handle True selection."""
        mock_run.return_value = Mock(stdout="True\n", returncode=0)

        param_info = {
            'name': 'enabled',
            'type': 'bool',
            'required': False,
            'default': True
        }

        result = prompt_for_boolean(param_info)
        assert result == "True"

        # Check gum choose was called
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert 'gum' in cmd
        assert 'choose' in cmd
        assert 'True' in cmd
        assert 'False' in cmd

    @patch('subprocess.run')
    def test_prompt_boolean_false(self, mock_run):
        """Should handle False selection."""
        mock_run.return_value = Mock(stdout="False\n", returncode=0)

        param_info = {
            'name': 'debug',
            'type': 'bool',
            'required': False,
            'default': False
        }

        result = prompt_for_boolean(param_info)
        assert result == "False"

    @patch('subprocess.run')
    def test_prompt_boolean_cancelled(self, mock_run):
        """Should use default when cancelled."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gum')

        param_info = {
            'name': 'active',
            'type': 'bool',
            'required': False,
            'default': True
        }

        result = prompt_for_boolean(param_info)
        assert result == "True"


class TestPromptForParameters:
    """Test prompting for all method parameters."""

    def sample_method(self, name: str, age: int = 25, active: bool = True):
        """Sample method for testing."""
        pass

    @patch('smpub.interactive.is_gum_available')
    def test_gum_not_available(self, mock_is_available):
        """Should exit with error message when gum not available."""
        mock_is_available.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            prompt_for_parameters(self.sample_method)

        assert exc_info.value.code == 1

    @patch('smpub.interactive.is_gum_available')
    @patch('smpub.interactive.prompt_for_parameter')
    @patch('smpub.interactive.prompt_for_boolean')
    def test_prompt_all_parameters(
        self, mock_bool_prompt, mock_param_prompt, mock_is_available
    ):
        """Should prompt for all parameters in order."""
        mock_is_available.return_value = True
        mock_param_prompt.side_effect = ["Alice", "30"]
        mock_bool_prompt.return_value = "True"

        result = prompt_for_parameters(self.sample_method)

        assert result == ["Alice", "30", "True"]
        assert mock_param_prompt.call_count == 2
        assert mock_bool_prompt.call_count == 1

    @patch('smpub.interactive.is_gum_available')
    def test_no_parameters(self, mock_is_available):
        """Should handle methods with no parameters."""
        mock_is_available.return_value = True

        def no_params_method():
            pass

        result = prompt_for_parameters(no_params_method)
        assert result == []

    @patch('smpub.interactive.is_gum_available')
    @patch('smpub.interactive.prompt_for_parameter')
    @patch('smpub.interactive.prompt_for_boolean')
    def test_mixed_types(self, mock_bool, mock_param, mock_is_available):
        """Should use appropriate prompt for each type."""
        mock_is_available.return_value = True
        mock_param.side_effect = ["test", "42", "3.14"]
        mock_bool.side_effect = ["True", "False"]

        def mixed_method(
            text: str,
            number: int,
            decimal: float,
            flag1: bool,
            flag2: bool = False
        ):
            pass

        result = prompt_for_parameters(mixed_method)

        # Should call param prompt for non-bool types
        assert mock_param.call_count == 3
        # Should call bool prompt for bool types
        assert mock_bool.call_count == 2
        # Results in correct order
        assert result == ["test", "42", "3.14", "True", "False"]
