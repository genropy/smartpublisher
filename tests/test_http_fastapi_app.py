"""Test http/fastapi_app.py module for comprehensive coverage."""

from fastapi.testclient import TestClient
from smpub import Publisher
from smartswitch import Switcher
from smpub.http.fastapi_app import create_fastapi_app


class TestHandler:
    """Test handler with various method types."""

    __test__ = False  # Not a pytest test class
    api = Switcher(prefix="test_")

    def __init__(self):
        self.data = {}

    @api
    def test_add(self, key: str, value: int):
        """Add a key-value pair.

        Args:
            key: The key
            value: The value
        """
        self.data[key] = value
        return f"Added {key}={value}"

    @api
    def test_get(self, key: str):
        """Get a value by key.

        Args:
            key: The key to retrieve
        """
        return self.data.get(key, "Not found")

    @api
    def test_optional(self, required: str, optional: int = 42):
        """Method with optional parameter.

        Args:
            required: Required parameter
            optional: Optional parameter with default
        """
        return {"required": required, "optional": optional}

    @api
    async def test_async(self, msg: str):
        """Async method.

        Args:
            msg: Message to return
        """
        return f"Async: {msg}"

    @api
    def test_error(self):
        """Method that raises an error."""
        raise RuntimeError("Test error")


class ErrorHandler:
    """Handler that will cause route creation issues."""

    api = Switcher(prefix="bad_")

    @api
    def bad_method(self, arg: str):
        """Method with non-standard naming."""
        return arg


class TestFastAPIApp:
    """Test FastAPI app creation."""

    def test_create_app_basic(self):
        """Should create FastAPI app from publisher."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)

        assert app is not None
        assert app.title == "TestApp"

    def test_create_app_with_custom_config(self):
        """Should accept custom FastAPI configuration."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(
            app_publisher,
            title="Custom Title",
            description="Custom Description",
            version="1.2.3",
            docs_url="/custom-docs",
        )

        assert app.title == "Custom Title"
        assert app.description == "Custom Description"
        assert app.version == "1.2.3"

    def test_routes_created_for_methods(self):
        """Should create routes for all published methods."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Test add method
        response = client.post("/handler/add", json={"key": "foo", "value": 123})
        assert response.status_code == 200
        assert response.json()["result"] == "Added foo=123"

    def test_get_method_works(self):
        """Should handle GET-like methods via POST."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Add data
        client.post("/handler/add", json={"key": "test", "value": 999})

        # Get data
        response = client.post("/handler/get", json={"key": "test"})
        assert response.status_code == 200
        assert response.json()["result"] == 999

    def test_optional_parameters(self):
        """Should handle methods with optional parameters."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # With default
        response = client.post("/handler/optional", json={"required": "test"})
        assert response.status_code == 200
        result = response.json()["result"]
        assert result["required"] == "test"
        assert result["optional"] == 42

        # Override default
        response = client.post("/handler/optional", json={"required": "test", "optional": 100})
        assert response.status_code == 200
        result = response.json()["result"]
        assert result["optional"] == 100

    def test_async_method_via_http(self):
        """Should handle async methods via HTTP."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        response = client.post("/handler/async", json={"msg": "hello"})
        assert response.status_code == 200
        assert response.json()["result"] == "Async: hello"

    def test_missing_required_parameter(self):
        """Should return 422 for missing required parameters."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Missing 'value' parameter
        response = client.post("/handler/add", json={"key": "test"})
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "Missing required parameter" in detail or "value" in str(detail)

    def test_validation_error(self):
        """Should return 422 for validation errors."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Invalid type for 'value' (string instead of int)
        response = client.post("/handler/add", json={"key": "test", "value": "not_an_int"})
        assert response.status_code == 422

    def test_method_raises_exception(self):
        """Should return 500 for method exceptions."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        response = client.post("/handler/error", json={})
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert detail["status"] == "error"
        assert "Test error" in detail["message"]

    def test_multiple_handlers(self):
        """Should handle multiple published handlers."""

        class Handler1:
            api = Switcher(prefix="h1_")

            @api
            def h1_method(self, value: str):
                """Handler 1 method."""
                return f"H1: {value}"

        class Handler2:
            api = Switcher(prefix="h2_")

            @api
            def h2_method(self, value: str):
                """Handler 2 method."""
                return f"H2: {value}"

        class TestApp(Publisher):
            def initialize(self):
                self.h1 = Handler1()
                self.h2 = Handler2()
                self.publish("handler1", self.h1)
                self.publish("handler2", self.h2)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Test handler1
        response = client.post("/handler1/method", json={"value": "test1"})
        assert response.status_code == 200
        assert response.json()["result"] == "H1: test1"

        # Test handler2
        response = client.post("/handler2/method", json={"value": "test2"})
        assert response.status_code == 200
        assert response.json()["result"] == "H2: test2"

    def test_custom_http_path(self):
        """Should respect custom HTTP paths."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler, http_path="/api/v1/custom")

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        response = client.post("/api/v1/custom/add", json={"key": "test", "value": 42})
        assert response.status_code == 200
        assert response.json()["result"] == "Added test=42"

    def test_openapi_false_not_exposed(self):
        """Should not expose handlers with openapi=False."""

        class TestApp(Publisher):
            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler, openapi=False)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Should not find route (no openapi handlers registered)
        response = client.post("/handler/add", json={"key": "test", "value": 42})
        assert response.status_code == 404

    def test_empty_body(self):
        """Should handle empty request body for methods without params."""

        class SimpleHandler:
            api = Switcher(prefix="simple_")

            @api
            def simple_no_params(self):
                """Method with no parameters."""
                return "No params!"

        class TestApp(Publisher):
            def initialize(self):
                self.handler = SimpleHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)
        client = TestClient(app)

        # Empty body
        response = client.post("/handler/no_params")
        assert response.status_code == 200
        assert response.json()["result"] == "No params!"

        # Explicit empty JSON
        response = client.post("/handler/no_params", json={})
        assert response.status_code == 200
        assert response.json()["result"] == "No params!"

    def test_route_handler_metadata(self):
        """Should set proper metadata on route handlers."""

        class TestApp(Publisher):
            """Test application for metadata."""

            def initialize(self):
                self.handler = TestHandler()
                self.publish("handler", self.handler)

        app_publisher = TestApp()
        app = create_fastapi_app(app_publisher)

        # Check OpenAPI schema has correct info
        openapi_schema = app.openapi()
        assert openapi_schema["info"]["title"] == "TestApp"

        # Check routes have tags
        paths = openapi_schema["paths"]
        for path_data in paths.values():
            for method_data in path_data.values():
                if "tags" in method_data:
                    assert "handler" in method_data["tags"]
