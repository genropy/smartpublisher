"""
Interactive parameter prompting using gum.
"""

import subprocess
import sys
from typing import Any
from .validation import get_parameter_info


def is_gum_available() -> bool:
    """
    Check if gum CLI tool is available.

    Returns:
        True if gum is installed and in PATH
    """
    try:
        subprocess.run(['gum', '--version'],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def prompt_for_parameter(param_info: dict[str, Any]) -> str:
    """
    Prompt user for a single parameter using gum.

    Args:
        param_info: Parameter info dict with keys: name, type, required, default

    Returns:
        User input as string

    Example:
        >>> param_info = {'name': 'age', 'type': 'int', 'required': False, 'default': 25}
        >>> value = prompt_for_parameter(param_info)
    """
    name = param_info['name']
    param_type = param_info['type']
    required = param_info['required']
    default = param_info['default']

    # Build prompt text
    prompt = f"{name} ({param_type})"
    if not required:
        prompt += f" [default: {default}]"
    prompt += ": "

    # Use gum input
    cmd = ['gum', 'input', '--placeholder', prompt]
    if not required and default is not None:
        cmd.extend(['--value', str(default)])

    try:
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              check=True)
        value = result.stdout.strip()

        # If empty and not required, use default
        if not value and not required:
            return str(default)

        return value
    except subprocess.CalledProcessError:
        # User cancelled or error
        print("\nCancelled.")
        sys.exit(0)


def prompt_for_boolean(param_info: dict[str, Any]) -> str:
    """
    Prompt user for a boolean parameter using gum choose.

    Args:
        param_info: Parameter info dict with keys: name, type, required, default

    Returns:
        'True' or 'False' as string

    Example:
        >>> param_info = {'name': 'enabled', 'type': 'bool', 'required': False, 'default': True}
        >>> value = prompt_for_boolean(param_info)
    """
    name = param_info['name']
    default = param_info.get('default', True)

    prompt = f"{name} (bool):"

    # Use gum choose for boolean
    cmd = ['gum', 'choose', 'True', 'False']

    try:
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              check=True)
        value = result.stdout.strip()
        return value
    except subprocess.CalledProcessError:
        # User cancelled, use default
        return str(default)


def prompt_for_parameters(method) -> list[str]:
    """
    Interactively prompt for all method parameters using gum.

    Args:
        method: The method to prompt for

    Returns:
        List of string values (in correct order)

    Example:
        >>> def test_method(name: str, age: int = 25, enabled: bool = True):
        ...     pass
        >>> args = prompt_for_parameters(test_method)
        >>> # User is prompted for each parameter
        >>> args
        ['Alice', '30', 'True']
    """
    # Check if gum is available
    if not is_gum_available():
        print("Error: gum is not installed or not in PATH")
        print("\nTo use interactive mode, install gum:")
        print("  macOS: brew install gum")
        print("  Linux: https://github.com/charmbracelet/gum#installation")
        sys.exit(1)

    # Get parameter info
    params = get_parameter_info(method)

    if not params:
        return []

    print("\nEnter parameters:\n")

    values = []
    for param_info in params:
        # Handle boolean parameters specially
        if param_info['type'] == 'bool':
            value = prompt_for_boolean(param_info)
        else:
            value = prompt_for_parameter(param_info)

        values.append(value)

    return values
