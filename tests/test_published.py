"""
Tests for published module (API discovery and PublisherContext).
"""

from unittest.mock import Mock

import pytest

from smartpublisher.published import discover_api_json, PublisherContext


class TestDiscoverApiJson:
    """Test API discovery from handlers."""

    def test_discover_from_instance(self):
        """Should discover API from handler instance."""

        class TestHandler:
            """Test handler class."""

            api = Mock()

            def test_method(self, name: str):
                """Test method."""
                pass

        # Mock Switcher
        handler = TestHandler()
        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.api = mock_switcher

        result = discover_api_json(handler)

        assert result["class"] == "TestHandler"
        assert result["description"] == "Test handler class."
        assert "method" in result["methods"]

    def test_discover_from_class(self):
        """Should discover API from handler class (not instance)."""

        class TestHandler:
            """Test handler class."""

            api = Mock()

            def test_method(self, value: int):
                """Test method."""
                pass

        # Mock Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.api = mock_switcher

        # Pass class directly (not instance)
        result = discover_api_json(TestHandler)

        assert result["class"] == "TestHandler"
        assert result["description"] == "Test handler class."
        assert "method" in result["methods"]

    def test_discover_class_without_switcher(self):
        """Should return empty methods for class without Switcher attribute."""

        class TestHandler:
            """Handler without Switcher."""

            pass

        result = discover_api_json(TestHandler)

        assert result["class"] == "TestHandler"
        assert result["description"] == "Handler without Switcher."
        assert result["methods"] == {}

    def test_discover_method_not_on_class(self):
        """Should skip methods that don't exist on the class."""

        class TestHandler:
            """Test handler."""

            api = Mock()

            def test_existing(self):
                """Existing method."""
                pass

        # Mock Switcher that references a non-existent method
        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["existing", "nonexistent"])
        TestHandler.api = mock_switcher

        result = discover_api_json(TestHandler)

        # Should only include the existing method
        assert "existing" in result["methods"]
        assert "nonexistent" not in result["methods"]

    def test_discover_method_signature_failure(self):
        """Should handle exceptions during signature extraction."""

        class TestHandler:
            """Test handler."""

            api = Mock()

        handler = TestHandler()

        # Create a mock method that will fail signature extraction
        # We'll create an object that looks like a method but raises on signature
        class BadMethod:
            """Method that breaks inspect.signature."""

            __doc__ = "Bad method"

            def __call__(self):
                pass

            def __repr__(self):
                raise RuntimeError("Cannot inspect")

        bad_method = BadMethod()

        # Manually attach it to the class
        TestHandler.test_bad = bad_method

        # Mock Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["bad"])
        TestHandler.api = mock_switcher

        # Even if signature extraction fails, should not crash
        # Just return method with empty parameters
        result = discover_api_json(handler)

        assert "bad" in result["methods"]
        assert result["methods"]["bad"]["parameters"] == []

    def test_discover_with_custom_switcher_name(self):
        """Should support custom switcher attribute name."""

        class TestHandler:
            """Test handler with custom switcher."""

            my_api = Mock()

            def method(self):
                """Method."""
                pass

        # Mock custom Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = ""
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.my_api = mock_switcher

        result = discover_api_json(TestHandler, switcher_name="my_api")

        assert "method" in result["methods"]

    def test_discover_method_with_parameters(self):
        """Should extract method parameters correctly."""

        class TestHandler:
            """Test handler."""

            api = Mock()

            def test_method(self, name: str, age: int = 25, active: bool = True):
                """Method with parameters."""
                pass

        # Mock Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.api = mock_switcher

        result = discover_api_json(TestHandler)

        params = result["methods"]["method"]["parameters"]
        assert len(params) == 3

        # Check name parameter (required)
        name_param = next(p for p in params if p["name"] == "name")
        assert name_param["type"] == "str"
        assert name_param["required"] is True
        assert name_param["default"] is None

        # Check age parameter (optional)
        age_param = next(p for p in params if p["name"] == "age")
        assert age_param["type"] == "int"
        assert age_param["required"] is False
        assert age_param["default"] == 25

        # Check active parameter (optional)
        active_param = next(p for p in params if p["name"] == "active")
        assert active_param["type"] == "bool"
        assert active_param["required"] is False
        assert active_param["default"] is True

    def test_discover_method_without_type_annotations(self):
        """Should handle methods without type annotations."""

        class TestHandler:
            """Test handler."""

            api = Mock()

            def test_method(self, value):
                """Method without annotations."""
                pass

        # Mock Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.api = mock_switcher

        result = discover_api_json(TestHandler)

        params = result["methods"]["method"]["parameters"]
        assert len(params) == 1
        assert params[0]["name"] == "value"
        assert params[0]["type"] == "Any"

    def test_discover_class_without_docstring(self):
        """Should handle class without docstring."""

        class TestHandler:
            api = Mock()

        mock_switcher = Mock()
        mock_switcher.prefix = ""
        mock_switcher.entries = Mock(return_value=[])
        TestHandler.api = mock_switcher

        result = discover_api_json(TestHandler)

        assert result["description"] == ""

    def test_discover_method_without_docstring(self):
        """Should handle method without docstring."""

        class TestHandler:
            """Handler."""

            api = Mock()

            def test_method(self):
                pass

        mock_switcher = Mock()
        mock_switcher.prefix = "test_"
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.api = mock_switcher

        result = discover_api_json(TestHandler)

        assert result["methods"]["method"]["description"] == ""


class TestPublisherContext:
    """Test PublisherContext class."""

    def test_init_default_switcher(self):
        """Should initialize with default switcher name."""
        handler = Mock()
        context = PublisherContext(handler)

        assert context._handler is handler
        assert context.parent_api is None
        assert context.switcher_name == "api"

    def test_init_custom_switcher(self):
        """Should initialize with custom switcher name."""
        handler = Mock()
        context = PublisherContext(handler, switcher_name="my_api")

        assert context.switcher_name == "my_api"

    def test_get_api_json_with_handler(self):
        """Should get API JSON for handler."""

        class TestHandler:
            """Test handler."""

            api = Mock()

            def method(self):
                """Method."""
                pass

        handler = TestHandler()

        # Mock Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = ""
        mock_switcher.entries = Mock(return_value=["method"])
        TestHandler.api = mock_switcher

        context = PublisherContext(handler)
        result = context.get_api_json()

        assert result["class"] == "TestHandler"
        assert "method" in result["methods"]

    def test_get_api_json_with_custom_target(self):
        """Should get API JSON for custom target."""

        class Handler1:
            """Handler 1."""

            api = Mock()

        class Handler2:
            """Handler 2."""

            api = Mock()

            def method(self):
                """Method."""
                pass

        handler1 = Handler1()
        handler2 = Handler2()

        # Mock Switchers
        mock_switcher1 = Mock()
        mock_switcher1.prefix = ""
        mock_switcher1.entries = Mock(return_value=[])
        Handler1.api = mock_switcher1

        mock_switcher2 = Mock()
        mock_switcher2.prefix = ""
        mock_switcher2.entries = Mock(return_value=["method"])
        Handler2.api = mock_switcher2

        context = PublisherContext(handler1)
        # Get API for handler2, not handler1
        result = context.get_api_json(target=handler2)

        assert result["class"] == "Handler2"
        assert "method" in result["methods"]

    def test_get_api_json_recursive_parameter(self):
        """Should accept recursive parameter (even if not yet implemented)."""

        class TestHandler:
            """Test handler."""

            api = Mock()

        handler = TestHandler()

        # Mock Switcher
        mock_switcher = Mock()
        mock_switcher.prefix = ""
        mock_switcher.entries = Mock(return_value=[])
        TestHandler.api = mock_switcher

        context = PublisherContext(handler)

        # Should not raise error
        result = context.get_api_json(recursive=True)
        assert result["class"] == "TestHandler"
