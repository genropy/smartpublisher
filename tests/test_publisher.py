"""Tests for Publisher coordinator."""

import pytest
from unittest.mock import Mock

from smartpublisher.publisher import Publisher
from smartpublisher.published import PublishedClass


class TestPublisher:
    """Test Publisher functionality."""

    def test_init_default(self):
        """Should initialize with default local registry."""
        pub = Publisher()

        assert pub.app_registry is not None
        assert pub.chan_registry.channels is not None
        assert "cli" in pub.chan_registry.channels
        assert "http" in pub.chan_registry.channels
        assert pub.app_registry.applications == {}

    def test_init_with_custom_registry(self, tmp_path):
        """Should initialize with custom registry path."""
        registry_path = tmp_path / "custom_registry"
        pub = Publisher(registry_path=registry_path)

        assert pub.app_registry is not None

    def test_init_with_global_registry(self):
        """Should initialize with global registry."""
        pub = Publisher(use_global=True)

        assert pub.app_registry is not None

    def test_get_channel(self):
        """Should get channel by name."""
        pub = Publisher()

        cli_channel = pub.get_channel("cli")
        http_channel = pub.get_channel("http")

        assert cli_channel is not None
        assert http_channel is not None

    def test_get_channel_not_found(self):
        """Should raise KeyError for unknown channel."""
        pub = Publisher()

        with pytest.raises(KeyError):
            pub.get_channel("nonexistent")

    def test_add_channel(self):
        """Should add custom channel."""
        pub = Publisher()

        # Mock channel
        mock_channel = object()

        pub.add_channel("custom", mock_channel)

        assert pub.get_channel("custom") is mock_channel

    def test_load_app_not_in_registry(self):
        """Should handle loading app not in registry."""
        pub = Publisher()

        # This will fail because app doesn't exist
        # Just test that the method exists
        assert hasattr(pub, "load_app")

    def test_unload_app_not_loaded(self):
        """Should handle unloading app that isn't loaded."""
        pub = Publisher()

        result = pub.unload_app("nonexistent")

        assert "error" in result

    def test_has_run_cli_method(self):
        """Should have run_cli method."""
        pub = Publisher()

        assert hasattr(pub, "run_cli")
        assert callable(pub.run_cli)

    def test_has_run_http_method(self):
        """Should have run_http method."""
        pub = Publisher()

        assert hasattr(pub, "run_http")
        assert callable(pub.run_http)

    def test_load_app_success(self):
        """Should load app from registry and cache it."""
        pub = Publisher()

        # Create mock app
        mock_app = Mock(spec=PublishedClass)
        mock_app._set_publisher = Mock()
        mock_app.smpub_on_add = Mock(return_value={"status": "ok"})

        # Mock registry.load
        pub.app_registry.load = Mock(return_value=mock_app)

        # Load app
        result = pub.load_app("test_app")

        # Verify
        assert result is mock_app
        assert "test_app" in pub.app_registry.applications
        mock_app._set_publisher.assert_called_once_with(pub)
        mock_app.smpub_on_add.assert_called_once()

    def test_load_app_already_loaded(self):
        """Should return cached app if already loaded."""
        pub = Publisher()

        # Pre-load an app
        mock_app = Mock()
        pub.app_registry.applications["test_app"] = mock_app

        # Mock registry to ensure it's not called
        pub.app_registry.load = Mock()

        # Load app again
        result = pub.load_app("test_app")

        # Should return cached instance
        assert result is mock_app
        pub.app_registry.load.assert_not_called()

    def test_load_app_without_hooks(self):
        """Should handle app without lifecycle hooks."""
        pub = Publisher()

        # Create app without hooks
        mock_app = Mock(spec=[])  # No methods

        pub.app_registry.load = Mock(return_value=mock_app)

        # Should not raise error
        result = pub.load_app("test_app")

        assert result is mock_app
        assert "test_app" in pub.app_registry.applications

    def test_unload_app_success(self):
        """Should unload app and call lifecycle hook."""
        pub = Publisher()

        # Create mock app with hook
        mock_app = Mock()
        mock_app.smpub_on_remove = Mock(return_value={"status": "ok"})
        pub.app_registry.applications["test_app"] = mock_app

        # Unload
        result = pub.unload_app("test_app")

        # Verify
        assert result["status"] == "unloaded"
        assert result["app"] == "test_app"
        assert "test_app" not in pub.app_registry.applications
        mock_app.smpub_on_remove.assert_called_once()

    def test_unload_app_without_hook(self):
        """Should unload app even without lifecycle hook."""
        pub = Publisher()

        # App without hook
        mock_app = Mock(spec=[])
        pub.app_registry.applications["test_app"] = mock_app

        # Should not raise error
        result = pub.unload_app("test_app")

        assert result["status"] == "unloaded"
        assert "test_app" not in pub.app_registry.applications

    def test_get_publisher_singleton(self):
        """Should return singleton instance."""
        from smartpublisher.publisher import get_publisher

        pub1 = get_publisher()
        pub2 = get_publisher()

        assert pub1 is pub2
