"""
Tests for validation module (Pydantic-based parameter validation).
"""

import pytest
from pydantic import ValidationError

from smpub.validation import (
    create_pydantic_model,
    validate_args,
    format_validation_error,
    get_parameter_info,
)


# Test fixtures - sample methods with various signatures
def method_no_params():
    """Method with no parameters."""
    pass


def method_required_only(name: str, age: int):
    """Method with only required parameters."""
    pass


def method_with_defaults(name: str, age: int = 25, active: bool = True):
    """Method with required and optional parameters."""
    pass


def method_all_types(
    text: str,
    number: int,
    decimal: float,
    flag: bool,
    count: int = 10,
):
    """Method with various types."""
    pass


class TestCreatePydanticModel:
    """Test dynamic Pydantic model generation from method signatures."""

    def test_no_parameters(self):
        """Should create model with no fields for method without parameters."""
        Model = create_pydantic_model(method_no_params)
        instance = Model()
        assert instance.model_dump() == {}

    def test_required_parameters(self):
        """Should create model with required fields."""
        Model = create_pydantic_model(method_required_only)

        # Valid data
        instance = Model(name="Alice", age=30)
        assert instance.name == "Alice"
        assert instance.age == 30

        # Missing required field should raise ValidationError
        with pytest.raises(ValidationError):
            Model(name="Alice")

    def test_optional_parameters(self):
        """Should handle default values correctly."""
        Model = create_pydantic_model(method_with_defaults)

        # With all parameters
        instance = Model(name="Alice", age=30, active=False)
        assert instance.name == "Alice"
        assert instance.age == 30
        assert instance.active is False

        # With defaults
        instance = Model(name="Bob")
        assert instance.name == "Bob"
        assert instance.age == 25
        assert instance.active is True

    def test_type_conversion(self):
        """Should convert string inputs to correct types."""
        Model = create_pydantic_model(method_all_types)

        # Pydantic should convert strings to proper types
        instance = Model(text="hello", number="42", decimal="3.14", flag="true")
        assert instance.text == "hello"
        assert instance.number == 42
        assert instance.decimal == 3.14
        assert instance.flag is True


class TestValidateArgs:
    """Test argument validation and conversion."""

    def test_validate_no_args(self):
        """Should handle methods with no parameters."""
        result = validate_args(method_no_params, [])
        assert result == {}

    def test_validate_required_args(self):
        """Should validate and convert required arguments."""
        result = validate_args(method_required_only, ["Alice", "30"])
        assert result == {"name": "Alice", "age": 30}

    def test_validate_with_defaults(self):
        """Should use defaults for missing optional parameters."""
        result = validate_args(method_with_defaults, ["Bob"])
        assert result == {"name": "Bob", "age": 25, "active": True}

        result = validate_args(method_with_defaults, ["Alice", "35"])
        assert result == {"name": "Alice", "age": 35, "active": True}

        result = validate_args(method_with_defaults, ["Charlie", "40", "False"])
        assert result == {"name": "Charlie", "age": 40, "active": False}

    def test_type_conversions(self):
        """Should convert string arguments to proper types."""
        result = validate_args(method_all_types, ["text", "42", "3.14", "true"])
        assert result["text"] == "text"
        assert result["number"] == 42
        assert isinstance(result["number"], int)
        assert result["decimal"] == 3.14
        assert isinstance(result["decimal"], float)
        assert result["flag"] is True
        assert isinstance(result["flag"], bool)

    def test_invalid_type(self):
        """Should raise ValidationError for invalid types."""
        with pytest.raises(ValidationError) as exc_info:
            validate_args(method_required_only, ["Alice", "not_a_number"])

        assert "age" in str(exc_info.value)

    def test_missing_required(self):
        """Should raise ValidationError for missing required parameters."""
        with pytest.raises(ValidationError) as exc_info:
            validate_args(method_required_only, [])

        error_dict = exc_info.value.errors()
        field_names = [e['loc'][0] for e in error_dict]
        assert "name" in field_names
        assert "age" in field_names

    def test_boolean_conversion(self):
        """Should handle various boolean representations."""
        # True values
        for true_val in ["True", "true", "1", "yes"]:
            result = validate_args(method_with_defaults, ["Test", "25", true_val])
            assert result["active"] is True

        # False values
        for false_val in ["False", "false", "0", "no"]:
            result = validate_args(method_with_defaults, ["Test", "25", false_val])
            assert result["active"] is False


class TestFormatValidationError:
    """Test error message formatting."""

    def test_format_single_error(self):
        """Should format single validation error clearly."""
        try:
            validate_args(method_required_only, ["Alice", "not_a_number"])
        except ValidationError as e:
            formatted = format_validation_error(e)
            assert "Validation errors:" in formatted
            assert "age" in formatted
            assert "integer" in formatted.lower()

    def test_format_multiple_errors(self):
        """Should format multiple validation errors."""
        try:
            validate_args(method_required_only, [])
        except ValidationError as e:
            formatted = format_validation_error(e)
            assert "Validation errors:" in formatted
            assert "name" in formatted
            assert "age" in formatted


class TestGetParameterInfo:
    """Test parameter information extraction."""

    def test_no_parameters(self):
        """Should return empty list for parameterless method."""
        info = get_parameter_info(method_no_params)
        assert info == []

    def test_required_parameters(self):
        """Should extract required parameter info."""
        info = get_parameter_info(method_required_only)

        assert len(info) == 2

        name_param = next(p for p in info if p['name'] == 'name')
        assert name_param['type'] == 'str'
        assert name_param['required'] is True
        assert name_param['default'] is None

        age_param = next(p for p in info if p['name'] == 'age')
        assert age_param['type'] == 'int'
        assert age_param['required'] is True
        assert age_param['default'] is None

    def test_optional_parameters(self):
        """Should extract optional parameter info with defaults."""
        info = get_parameter_info(method_with_defaults)

        assert len(info) == 3

        name_param = next(p for p in info if p['name'] == 'name')
        assert name_param['required'] is True

        age_param = next(p for p in info if p['name'] == 'age')
        assert age_param['required'] is False
        assert age_param['default'] == 25

        active_param = next(p for p in info if p['name'] == 'active')
        assert active_param['required'] is False
        assert active_param['default'] is True

    def test_type_names(self):
        """Should extract correct type names."""
        info = get_parameter_info(method_all_types)

        types = {p['name']: p['type'] for p in info}
        assert types['text'] == 'str'
        assert types['number'] == 'int'
        assert types['decimal'] == 'float'
        assert types['flag'] == 'bool'
