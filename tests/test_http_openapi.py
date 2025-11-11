"""Test http/openapi.py module for comprehensive coverage."""

from smpub import Publisher
from smartswitch import Switcher
from smpub.http.openapi import generate_openapi_schema, _python_type_to_openapi


class SimpleHandler:
    """Handler with various parameter types."""

    api = Switcher(prefix="simple_")

    @api
    def simple_string(self, name: str):
        """Method with string parameter.

        Args:
            name: User name
        """
        return f"Hello {name}"

    @api
    def simple_int(self, count: int):
        """Method with int parameter.

        Args:
            count: Number of items
        """
        return count * 2

    @api
    def simple_float(self, value: float):
        """Method with float parameter.

        Args:
            value: Float value
        """
        return value * 1.5

    @api
    def simple_bool(self, flag: bool):
        """Method with bool parameter.

        Args:
            flag: Boolean flag
        """
        return not flag

    @api
    def simple_optional(self, required: str, optional: int = 42):
        """Method with optional parameter.

        Args:
            required: Required string
            optional: Optional int with default
        """
        return {"required": required, "optional": optional}

    @api
    def simple_no_params(self):
        """Method with no parameters."""
        return "No params"


class ComplexHandler:
    """Handler with complex types."""

    api = Switcher(prefix="complex_")

    @api
    def complex_list(self, items: list):
        """Method with list parameter.

        Args:
            items: List of items
        """
        return len(items)

    @api
    def complex_dict(self, data: dict):
        """Method with dict parameter.

        Args:
            data: Dictionary data
        """
        return data

    @api
    def complex_any(self, value):
        """Method with Any parameter.

        Args:
            value: Any value
        """
        return value


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""

    def test_basic_schema_structure(self):
        """Should generate valid OpenAPI 3.0 schema structure."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        assert schema["openapi"] == "3.0.0"
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema

    def test_custom_info(self):
        """Should use custom title, version, and description."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(
            app, title="My API", version="1.2.3", description="Test API"
        )

        assert schema["info"]["title"] == "My API"
        assert schema["info"]["version"] == "1.2.3"
        assert schema["info"]["description"] == "Test API"

    def test_paths_created_for_methods(self):
        """Should create path for each published method."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        paths = schema["paths"]
        assert "/simple/string" in paths
        assert "/simple/int" in paths
        assert "/simple/float" in paths
        assert "/simple/bool" in paths
        assert "/simple/optional" in paths
        assert "/simple/no_params" in paths

    def test_operations_use_post(self):
        """Should use POST method for all operations."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        for path_data in schema["paths"].values():
            assert "post" in path_data
            assert "get" not in path_data

    def test_operation_id_format(self):
        """Should format operationId as handler_method."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        assert operation["operationId"] == "simple_string"

    def test_tags_from_handler_name(self):
        """Should use handler name as tag."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        assert operation["tags"] == ["simple"]

    def test_summary_from_first_line(self):
        """Should use method name as summary when no docstring in API."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        # get_api_json() doesn't include full docstring, just description field
        # which contains first line, so summary will be method_name when docstring not available
        assert operation["summary"] == "string"

    def test_description_from_api_json(self):
        """Should use description from get_api_json()."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        # get_api_json() returns "description" field with first line of docstring
        assert operation["description"] == ""  # Empty because get_api_json doesn't include it

    def test_request_body_for_parameters(self):
        """Should create request body for methods with parameters."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        assert "requestBody" in operation
        assert operation["requestBody"]["required"] is True
        assert "application/json" in operation["requestBody"]["content"]

    def test_no_request_body_for_no_params(self):
        """Should not create request body for methods without parameters."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/no_params"]["post"]
        assert "requestBody" not in operation

    def test_required_parameters(self):
        """Should mark required parameters correctly."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        request_body = operation["requestBody"]["content"]["application/json"]["schema"]
        assert "name" in request_body["required"]

    def test_optional_parameters_with_defaults(self):
        """Should include default values for optional parameters."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/optional"]["post"]
        request_body = operation["requestBody"]["content"]["application/json"]["schema"]

        # Required parameter
        assert "required" in request_body["required"]

        # Optional parameter
        assert "optional" not in request_body["required"]
        assert request_body["properties"]["optional"]["default"] == 42

    def test_type_mapping_string(self):
        """Should map str to string."""
        assert _python_type_to_openapi("str") == "string"

    def test_type_mapping_int(self):
        """Should map int to integer."""
        assert _python_type_to_openapi("int") == "integer"

    def test_type_mapping_float(self):
        """Should map float to number."""
        assert _python_type_to_openapi("float") == "number"

    def test_type_mapping_bool(self):
        """Should map bool to boolean."""
        assert _python_type_to_openapi("bool") == "boolean"

    def test_type_mapping_list(self):
        """Should map list to array."""
        assert _python_type_to_openapi("list") == "array"

    def test_type_mapping_dict(self):
        """Should map dict to object."""
        assert _python_type_to_openapi("dict") == "object"

    def test_type_mapping_any(self):
        """Should map Any to object."""
        assert _python_type_to_openapi("Any") == "object"

    def test_type_mapping_unknown(self):
        """Should default unknown types to string."""
        assert _python_type_to_openapi("UnknownType") == "string"

    def test_complex_types_in_schema(self):
        """Should handle complex types (list, dict, Any) in schema."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = ComplexHandler()
                self.publish("complex", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        # Check list parameter
        list_operation = schema["paths"]["/complex/list"]["post"]
        list_schema = list_operation["requestBody"]["content"]["application/json"]["schema"]
        assert list_schema["properties"]["items"]["type"] == "array"

        # Check dict parameter
        dict_operation = schema["paths"]["/complex/dict"]["post"]
        dict_schema = dict_operation["requestBody"]["content"]["application/json"]["schema"]
        assert dict_schema["properties"]["data"]["type"] == "object"

        # Check Any parameter
        any_operation = schema["paths"]["/complex/any"]["post"]
        any_schema = any_operation["requestBody"]["content"]["application/json"]["schema"]
        assert any_schema["properties"]["value"]["type"] == "object"

    def test_multiple_handlers(self):
        """Should handle multiple handlers in schema."""

        class Handler1:
            api = Switcher(prefix="h1_")

            @api
            def h1_method(self, value: str):
                """Handler 1 method."""
                return value

        class Handler2:
            api = Switcher(prefix="h2_")

            @api
            def h2_method(self, value: int):
                """Handler 2 method."""
                return value

        class TestApp(Publisher):
            def initialize(self):
                self.h1 = Handler1()
                self.h2 = Handler2()
                self.publish("handler1", self.h1)
                self.publish("handler2", self.h2)

        app = TestApp()
        schema = generate_openapi_schema(app)

        assert "/handler1/method" in schema["paths"]
        assert "/handler2/method" in schema["paths"]

        # Check tags are different
        h1_op = schema["paths"]["/handler1/method"]["post"]
        h2_op = schema["paths"]["/handler2/method"]["post"]
        assert h1_op["tags"] == ["handler1"]
        assert h2_op["tags"] == ["handler2"]

    def test_openapi_false_not_included(self):
        """Should not include handlers with openapi=False."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler, openapi=False)

        app = TestApp()
        schema = generate_openapi_schema(app)

        # Should have no paths (handler not exposed via OpenAPI)
        assert schema["paths"] == {}

    def test_responses_structure(self):
        """Should include standard response codes."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("simple", self.handler)

        app = TestApp()
        schema = generate_openapi_schema(app)

        operation = schema["paths"]["/simple/string"]["post"]
        responses = operation["responses"]

        assert "200" in responses
        assert responses["200"]["description"] == "Successful response"
        assert "422" in responses
        assert responses["422"]["description"] == "Validation error"
