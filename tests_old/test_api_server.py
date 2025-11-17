"""
Tests for api_server module (FastAPI integration).
"""

from enum import Enum
from unittest.mock import Mock

import pytest

# Import FastAPI components - handle optional dependency
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from pydantic import BaseModel, ValidationError

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from smartpublisher import api_server


def create_mock_switcher(handler, method_names, prefix=None):
    """
    Helper to create a mock switcher for tests.

    Args:
        handler: Handler instance with methods
        method_names: List of method names to expose
        prefix: Optional prefix for method names

    Returns:
        Configured Mock switcher
    """
    mock_switcher = Mock()
    mock_switcher.prefix = prefix
    mock_switcher.entries = Mock(return_value=method_names)

    # Configure .get() to return a callable that accepts (handler_instance, *args, **kwargs)
    # This mimics smartswitch behavior where methods are class-level (unbound)
    def get_method(name, **kwargs):
        # Return a wrapper that accepts handler as first arg
        def wrapper(handler_instance, *args, **kw):
            # Apply prefix if present
            full_name = f"{prefix}{name}" if prefix else name
            method = getattr(handler_instance, full_name)
            return method(*args, **kw)

        return wrapper

    mock_switcher.get = Mock(side_effect=get_method)
    return mock_switcher


class TestCreateFastAPIApp:
    """Test FastAPI app creation from Publisher."""

    def test_import_error_when_fastapi_not_installed(self):
        """Should raise ImportError if FastAPI not installed."""
        # Temporarily set FastAPI to None to simulate missing dependency
        original_fastapi = api_server.FastAPI
        api_server.FastAPI = None

        try:
            mock_publisher = Mock()
            with pytest.raises(ImportError, match="FastAPI is not installed"):
                api_server.create_fastapi_app(mock_publisher)
        finally:
            api_server.FastAPI = original_fastapi

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_create_app_with_defaults(self):
        """Should create FastAPI app with default parameters."""
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {}

        app = api_server.create_fastapi_app(mock_publisher)

        assert isinstance(app, FastAPI)
        assert app.title == "SmartPublisher API"
        assert app.description == "Auto-generated API from Publisher"
        assert app.version == "0.1.0"

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_create_app_with_custom_params(self):
        """Should create FastAPI app with custom parameters."""
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {}

        app = api_server.create_fastapi_app(
            mock_publisher,
            title="My API",
            description="Custom description",
            version="2.0.0",
        )

        assert app.title == "My API"
        assert app.description == "Custom description"
        assert app.version == "2.0.0"

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_root_endpoint_exists(self):
        """Should create root endpoint with documentation links."""
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {}

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Swagger UI" in response.text
        assert "ReDoc" in response.text
        assert "/docs" in response.text
        assert "/redoc" in response.text


class TestEndpointRegistration:
    """Test endpoint registration for handlers."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_simple_endpoint_no_parameters(self):
        """Should register simple GET endpoint for method without parameters."""
        # Create a mock handler with a simple method
        class TestHandler:
            api = Mock()

            def test_method(self):
                return "test result"

        handler = TestHandler()
        TestHandler.api = create_mock_switcher(handler, ["test_method"])

        # Create mock publisher
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/test/test_method")
        assert response.status_code == 200
        assert response.json() == {"result": "test result"}

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_get_endpoint_with_parameters(self):
        """Should register GET endpoint with query parameters for read-only methods."""

        # Create Pydantic model for parameters
        class TestRequestModel(BaseModel):
            name: str
            age: int = 25

        # Create handler with method that has Pydantic metadata
        class TestHandler:
            api = Mock()

            def list(self, name: str, age: int = 25):
                return {"name": name, "age": age}

        handler = TestHandler()

        # Add Pydantic metadata to method (use __func__ to access underlying function)
        handler.list.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["list"])

        # Create mock publisher
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        # For GET with parameters, FastAPI converts them to query params
        response = client.get("/test/list?name=Alice&age=30")
        assert response.status_code == 200
        assert response.json() == {"result": {"name": "Alice", "age": 30}}

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_post_endpoint_with_body(self):
        """Should register POST endpoint with request body for write methods."""

        class TestRequestModel(BaseModel):
            key: str
            value: str

        class TestHandler:
            api = Mock()

            def test_add(self, key: str, value: str):
                return {"added": key, "value": value}

        handler = TestHandler()
        handler.test_add.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["add"], prefix="test_")

        # Create mock publisher
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.post("/test/add", json={"key": "test", "value": "data"})
        assert response.status_code == 200
        assert response.json() == {"result": {"added": "test", "value": "data"}}


class TestResponseFormats:
    """Test different response formats (HTML, markdown, plain text)."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_html_response_format(self):
        """Should return HTMLResponse for format=html."""

        class TestRequestModel(BaseModel):
            format: str = "json"

        class TestHandler:
            api = Mock()

            def test_get(self, format: str = "json"):
                if format == "html":
                    return "<html><body>Test</body></html>"
                return {"data": "test"}

        handler = TestHandler()
        handler.test_get.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["get"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/test/get?format=html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Test" in response.text

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_markdown_html_response_format(self):
        """Should return HTML with markdown rendering for format=markdown_html."""

        class TestRequestModel(BaseModel):
            format: str = "json"

        class TestHandler:
            api = Mock()

            def test_get(self, format: str = "json"):
                if format in ("markdown", "markdown_html"):
                    return "# Test Markdown\n\nSome **bold** text"
                return {"data": "test"}

        handler = TestHandler()
        handler.test_get.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["get"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/test/get?format=markdown_html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "marked.parse" in response.text  # Markdown JS library
        assert "Test Markdown" in response.text

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_plain_text_response_format(self):
        """Should return PlainTextResponse for text format."""

        class TestRequestModel(BaseModel):
            format: str = "json"

        class TestHandler:
            api = Mock()

            def test_get(self, format: str = "json"):
                if format == "text":
                    return "Plain text response"
                return {"data": "test"}

        handler = TestHandler()
        handler.test_get.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["get"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/test/get?format=text")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert response.text == "Plain text response"


class TestEnumHandling:
    """Test handling of Enum parameters."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_enum_parameter_conversion(self):
        """Should convert Enum values to strings when calling methods."""

        class StatusEnum(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class TestRequestModel(BaseModel):
            status: StatusEnum

        class TestHandler:
            api = Mock()

            def test_add(self, status: str):
                # Method expects string, not Enum
                return {"status": status, "type": type(status).__name__}

        handler = TestHandler()
        handler.test_add.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["add"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.post("/test/add", json={"status": "active"})
        assert response.status_code == 200
        result = response.json()["result"]
        assert result["status"] == "active"
        assert result["type"] == "str"  # Should be converted to string


class TestErrorHandling:
    """Test error handling in endpoints."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_validation_error_returns_422(self):
        """Should return 422 for validation errors."""

        class TestRequestModel(BaseModel):
            age: int

        class TestHandler:
            api = Mock()

            def test_add(self, age: int):
                return {"age": age}

        handler = TestHandler()
        handler.test_add.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["add"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        # Invalid type for age
        response = client.post("/test/add", json={"age": "not_a_number"})
        assert response.status_code == 422

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_generic_exception_returns_500(self):
        """Should return 500 for generic exceptions."""

        class TestRequestModel(BaseModel):
            value: str

        class TestHandler:
            api = Mock()

            def test_add(self, value: str):
                raise RuntimeError("Something went wrong")

        handler = TestHandler()
        handler.test_add.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["add"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.post("/test/add", json={"value": "test"})
        assert response.status_code == 500
        assert "Something went wrong" in response.json()["detail"]


class TestAsyncMethods:
    """Test handling of async methods."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_async_method_support(self):
        """Should handle async methods correctly."""

        class TestHandler:
            api = Mock()

            async def test_method(self):
                return "async result"

        handler = TestHandler()

        TestHandler.api = create_mock_switcher(handler, ["method"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/test/method")
        assert response.status_code == 200
        assert response.json() == {"result": "async result"}

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_async_method_with_parameters(self):
        """Should handle async methods with parameters."""

        class TestRequestModel(BaseModel):
            name: str

        class TestHandler:
            api = Mock()

            async def test_add(self, name: str):
                return {"name": name}

        handler = TestHandler()
        handler.test_add.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["add"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.post("/test/add", json={"name": "Alice"})
        assert response.status_code == 200
        assert response.json() == {"result": {"name": "Alice"}}


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_custom_openapi_schema(self):
        """Should generate custom OpenAPI schema with model definitions."""

        class TestRequestModel(BaseModel):
            name: str
            age: int

        class TestHandler:
            api = Mock()

            def test_add(self, name: str, age: int):
                return {"name": name, "age": age}

        handler = TestHandler()
        handler.test_add.__func__._plugin_meta = {
            "pydantic": {"model": TestRequestModel}
        }

        TestHandler.api = create_mock_switcher(handler, ["add"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "SmartPublisher API"
        assert "/test/add" in schema["paths"]

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_openapi_schema_cached(self):
        """Should cache OpenAPI schema after first generation."""
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {}

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        # First call generates schema
        response1 = client.get("/openapi.json")
        schema1 = response1.json()

        # Second call should return cached schema
        response2 = client.get("/openapi.json")
        schema2 = response2.json()

        assert schema1 == schema2


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_handler_without_switcher(self):
        """Should skip handler if switcher attribute doesn't exist."""

        class TestHandler:
            pass  # No 'api' attribute

        handler = TestHandler()

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        # Should not raise error, just skip this handler
        app = api_server.create_fastapi_app(mock_publisher)
        assert isinstance(app, FastAPI)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_method_not_on_handler(self):
        """Should skip method if it doesn't exist on handler."""

        class TestHandler:
            api = Mock()

        handler = TestHandler()

        TestHandler.api = create_mock_switcher(handler, ["nonexistent_method"])

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        # Should not raise error, just skip this method
        app = api_server.create_fastapi_app(mock_publisher)
        assert isinstance(app, FastAPI)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_method_without_pydantic_metadata(self):
        """Should create endpoint even without Pydantic metadata."""

        class TestHandler:
            api = Mock()

            def test_method(self):
                return "result"

        handler = TestHandler()

        TestHandler.api = create_mock_switcher(handler, ["method"], prefix="test_")

        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {
            "/test": {
                "handler": handler,
                "name": "test",
                "switcher_name": "api",
            }
        }

        app = api_server.create_fastapi_app(mock_publisher)
        client = TestClient(app)

        response = client.get("/test/method")
        assert response.status_code == 200
        assert response.json() == {"result": "result"}

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_empty_handlers_dict(self):
        """Should create valid app even with no handlers."""
        mock_publisher = Mock()
        mock_publisher._openapi_handlers = {}

        app = api_server.create_fastapi_app(mock_publisher)
        assert isinstance(app, FastAPI)

        # Should still have root endpoint
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
