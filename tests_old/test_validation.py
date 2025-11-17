"""
Tests for validation module (Pydantic-based parameter validation).
"""

import pytest
from pydantic import ValidationError

from smartpublisher.validation import (
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
        field_names = [e["loc"][0] for e in error_dict]
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

        name_param = next(p for p in info if p["name"] == "name")
        assert name_param["type"] == "str"
        assert name_param["required"] is True
        assert name_param["default"] is None

        age_param = next(p for p in info if p["name"] == "age")
        assert age_param["type"] == "int"
        assert age_param["required"] is True
        assert age_param["default"] is None

    def test_optional_parameters(self):
        """Should extract optional parameter info with defaults."""
        info = get_parameter_info(method_with_defaults)

        assert len(info) == 3

        name_param = next(p for p in info if p["name"] == "name")
        assert name_param["required"] is True

        age_param = next(p for p in info if p["name"] == "age")
        assert age_param["required"] is False
        assert age_param["default"] == 25

        active_param = next(p for p in info if p["name"] == "active")
        assert active_param["required"] is False
        assert active_param["default"] is True

    def test_type_names(self):
        """Should extract correct type names."""
        info = get_parameter_info(method_all_types)

        types = {p["name"]: p["type"] for p in info}
        assert types["text"] == "str"
        assert types["number"] == "int"
        assert types["decimal"] == "float"
        assert types["flag"] == "bool"


# Additional test methods for better coverage
class TestParseDocstringParams:
    """Test docstring parameter parsing."""

    def test_empty_docstring(self):
        """Should return empty dict for None/empty docstring."""
        from smartpublisher.validation import parse_docstring_params

        assert parse_docstring_params(None) == {}
        assert parse_docstring_params("") == {}

    def test_simple_args_section(self):
        """Should parse simple Args section."""
        from smartpublisher.validation import parse_docstring_params

        docstring = """
        Some method description.

        Args:
            name: The user's name
            age: The user's age
        """
        params = parse_docstring_params(docstring)

        assert "name" in params
        assert params["name"] == "The user's name"
        assert "age" in params
        assert params["age"] == "The user's age"

    def test_args_with_types(self):
        """Should parse Args with type annotations."""
        from smartpublisher.validation import parse_docstring_params

        docstring = """
        Args:
            name (str): The user's name
            age (int): The user's age
        """
        params = parse_docstring_params(docstring)

        assert params["name"] == "The user's name"
        assert params["age"] == "The user's age"

    def test_multiline_descriptions(self):
        """Should handle multiline parameter descriptions."""
        from smartpublisher.validation import parse_docstring_params

        docstring = """
        Args:
            name: The user's name
                which can be very long
                and span multiple lines
            age: The age
        """
        params = parse_docstring_params(docstring)

        assert "name" in params
        assert "which can be very long" in params["name"]
        assert "and span multiple lines" in params["name"]
        assert "age" in params

    def test_args_section_terminated_by_next_section(self):
        """Should stop parsing at next section."""
        from smartpublisher.validation import parse_docstring_params

        docstring = """
        Args:
            name: The user's name

        Returns:
            Something else
        """
        params = parse_docstring_params(docstring)

        assert "name" in params
        assert "Returns" not in params

    def test_no_args_section(self):
        """Should return empty dict if no Args section."""
        from smartpublisher.validation import parse_docstring_params

        docstring = """
        Just a description.

        Returns:
            Something
        """
        params = parse_docstring_params(docstring)

        assert params == {}


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_method_with_self_parameter(self):
        """Should skip 'self' parameter in instance methods."""

        class TestClass:
            def instance_method(self, name: str, age: int = 25):
                """Instance method."""
                pass

        Model = create_pydantic_model(TestClass.instance_method)
        instance = Model(name="Alice", age=30)

        # Should have fields for name and age, but not self
        assert instance.name == "Alice"
        assert instance.age == 30
        assert not hasattr(instance, "self")

    def test_get_parameter_info_skips_self(self):
        """Should skip 'self' in parameter info."""

        class TestClass:
            def instance_method(self, name: str):
                pass

        info = get_parameter_info(TestClass.instance_method)

        # Should only have 'name', not 'self'
        assert len(info) == 1
        assert info[0]["name"] == "name"

    def test_complex_type_annotations(self):
        """Should handle Optional and Union types."""
        from typing import Optional, Union

        def method_with_optional(value: Optional[str] = None, number: Union[int, float] = 0):
            pass

        info = get_parameter_info(method_with_optional)

        assert len(info) == 2
        # Type should be string representation of the annotation
        assert "Optional" in info[0]["type"] or "str" in info[0]["type"]

    def test_method_with_no_type_annotations(self):
        """Should handle methods without type annotations."""

        def method_no_types(name, age=25):
            pass

        Model = create_pydantic_model(method_no_types)
        instance = Model(name="Alice", age=30)

        assert instance.name == "Alice"
        assert instance.age == 30

        # get_parameter_info should show 'Any' for untyped params
        info = get_parameter_info(method_no_types)
        assert info[0]["type"] == "Any"
        assert info[1]["type"] == "Any"
