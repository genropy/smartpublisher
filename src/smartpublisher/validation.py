"""
Validation utilities using Pydantic.
"""

import inspect
import re
from typing import Any, get_origin
from pydantic import BaseModel, ValidationError, create_model


def parse_docstring_params(docstring: str) -> dict[str, str]:
    """
    Parse parameter descriptions from docstring.

    Args:
        docstring: Method docstring

    Returns:
        Dictionary mapping parameter names to descriptions
    """
    if not docstring:
        return {}

    params = {}
    in_args_section = False
    current_param = None
    current_desc = []

    for line in docstring.split("\n"):
        line = line.strip()

        # Check if we're entering Args section
        if line.startswith("Args:"):
            in_args_section = True
            continue

        # Exit Args section on next section or empty line after params
        if in_args_section and line and not line.startswith(" ") and ":" not in line:
            break

        if in_args_section:
            # Match parameter line: "    name: description" or "    name (type): description"
            match = re.match(r"^\s*(\w+)(?:\s*\([^)]+\))?\s*:\s*(.+)$", line)
            if match:
                # Save previous parameter
                if current_param:
                    params[current_param] = " ".join(current_desc).strip()

                # Start new parameter
                current_param = match.group(1)
                current_desc = [match.group(2)]
            elif current_param and line:
                # Continuation of previous parameter description
                current_desc.append(line)

    # Save last parameter
    if current_param:
        params[current_param] = " ".join(current_desc).strip()

    return params


def create_pydantic_model(method) -> type[BaseModel]:
    """
    Create a Pydantic model from a method signature.

    Args:
        method: The method to introspect

    Returns:
        A Pydantic model class with fields matching method parameters

    Example:
        >>> def test_method(name: str, age: int = 25):
        ...     pass
        >>> Model = create_pydantic_model(test_method)
        >>> validated = Model(name="Alice", age="30")
        >>> validated.age  # Returns int 30, not str "30"
        30
    """
    sig = inspect.signature(method)
    fields = {}

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        # Get type annotation
        annotation = param.annotation if param.annotation != inspect.Parameter.empty else Any

        # Handle default values
        if param.default == inspect.Parameter.empty:
            # Required parameter - no default
            fields[param_name] = (annotation, ...)
        else:
            # Optional parameter with default
            fields[param_name] = (annotation, param.default)

    # Create dynamic model
    model_name = f"{method.__name__}_Model"
    return create_model(model_name, **fields)


def validate_args(method, args: list[str]) -> dict[str, Any]:
    """
    Validate and convert CLI arguments using Pydantic.

    Args:
        method: The method to validate against
        args: List of string arguments from CLI

    Returns:
        Dictionary of validated and converted parameters

    Raises:
        ValidationError: If validation fails

    Example:
        >>> def test_method(name: str, age: int = 25):
        ...     pass
        >>> validated = validate_args(test_method, ["Alice", "30"])
        >>> validated
        {'name': 'Alice', 'age': 30}
    """
    # Create Pydantic model
    Model = create_pydantic_model(method)

    # Get parameter names (excluding 'self')
    sig = inspect.signature(method)
    param_names = [name for name in sig.parameters.keys() if name != "self"]

    # Build kwargs dict from positional args
    kwargs = {}
    for i, value in enumerate(args):
        if i < len(param_names):
            kwargs[param_names[i]] = value

    # Validate with Pydantic
    validated = Model(**kwargs)

    # Return as dict
    return validated.model_dump()


def format_validation_error(error: ValidationError) -> str:
    """
    Format a Pydantic ValidationError for CLI display.

    Args:
        error: The ValidationError to format

    Returns:
        Human-readable error message

    Example:
        >>> try:
        ...     validate_args(test_method, ["Alice", "not_a_number"])
        ... except ValidationError as e:
        ...     print(format_validation_error(e))
        Validation errors:
          age: Input should be a valid integer...
    """
    lines = ["Validation errors:"]
    for err in error.errors():
        field = ".".join(str(x) for x in err["loc"])
        message = err["msg"]
        lines.append(f"  {field}: {message}")
    return "\n".join(lines)


def get_parameter_info(method) -> list[dict[str, Any]]:
    """
    Extract parameter information from a method signature.

    Args:
        method: The method to introspect

    Returns:
        List of parameter info dicts with keys:
        - name: Parameter name
        - type: Type annotation name
        - required: Whether parameter is required
        - default: Default value if not required

    Example:
        >>> def test_method(name: str, age: int = 25):
        ...     pass
        >>> get_parameter_info(test_method)
        [
            {'name': 'name', 'type': 'str', 'required': True, 'default': None},
            {'name': 'age', 'type': 'int', 'required': False, 'default': 25}
        ]
    """
    sig = inspect.signature(method)
    params = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        # Get type annotation
        param_type = "Any"
        if param.annotation != inspect.Parameter.empty:
            annotation = param.annotation
            # Handle Optional, Union, etc.
            origin = get_origin(annotation)
            if origin is not None:
                param_type = str(annotation)
            else:
                param_type = (
                    annotation.__name__ if hasattr(annotation, "__name__") else str(annotation)
                )

        # Check if required
        required = param.default == inspect.Parameter.empty
        default = None if required else param.default

        params.append(
            {"name": param_name, "type": param_type, "required": required, "default": default}
        )

    return params
