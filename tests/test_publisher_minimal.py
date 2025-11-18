"""Minimal test for Publisher basic functionality."""

import pytest
from pathlib import Path

from smartpublisher.publisher import Publisher


class TestPublisherMinimal:
    """Test Publisher with minimal registry operations."""

    def test_publisher_init(self, tmp_path):
        """Should initialize Publisher with registry."""
        registry_file = tmp_path / "apps.json"
        publisher = Publisher(registry_path=registry_file)

        assert publisher.app_registry is not None
        assert publisher.chan_registry.channels is not None
        assert 'cli' in publisher.chan_registry.channels
        assert 'http' in publisher.chan_registry.channels
        assert publisher.app_registry.applications == {}

    def test_list_empty_apps(self, tmp_path):
        """Should list zero apps initially."""
        registry_file = tmp_path / "apps.json"
        publisher = Publisher(registry_path=registry_file)

        result = publisher.app_registry.list()

        assert result['total'] == 0
        assert result['apps'] == {}

    def test_add_app(self, tmp_path):
        """Should add an app to registry."""
        registry_file = tmp_path / "apps.json"
        publisher = Publisher(registry_path=registry_file)

        # Create app directory
        app_dir = tmp_path / "testapp"
        app_dir.mkdir()

        # Add app
        result = publisher.app_registry.add(
            name='testapp',
            path=str(app_dir),
            module='main',
            class_name='TestApp'
        )

        assert result['status'] == 'registered'
        assert result['name'] == 'testapp'

        # Verify it's in the list
        apps = publisher.app_registry.list()
        assert apps['total'] == 1
        assert 'testapp' in apps['apps']

    def test_remove_app(self, tmp_path):
        """Should remove an app from registry."""
        registry_file = tmp_path / "apps.json"
        publisher = Publisher(registry_path=registry_file)

        # Create app directory
        app_dir = tmp_path / "testapp"
        app_dir.mkdir()

        # Add app
        publisher.app_registry.add(
            name='testapp',
            path=str(app_dir)
        )

        # Remove app
        result = publisher.app_registry.remove(name='testapp')

        assert result['status'] == 'removed'
        assert result['name'] == 'testapp'

        # Verify it's gone
        apps = publisher.app_registry.list()
        assert apps['total'] == 0
        assert 'testapp' not in apps['apps']

    def test_add_remove_multiple_apps(self, tmp_path):
        """Should handle multiple apps."""
        registry_file = tmp_path / "apps.json"
        publisher = Publisher(registry_path=registry_file)

        # Create app directories
        (tmp_path / "app1").mkdir()
        (tmp_path / "app2").mkdir()
        (tmp_path / "app3").mkdir()

        # Add multiple apps
        publisher.app_registry.add(name='app1', path=str(tmp_path / "app1"))
        publisher.app_registry.add(name='app2', path=str(tmp_path / "app2"))
        publisher.app_registry.add(name='app3', path=str(tmp_path / "app3"))

        # Verify count
        apps = publisher.app_registry.list()
        assert apps['total'] == 3

        # Remove one
        publisher.app_registry.remove(name='app2')

        # Verify count
        apps = publisher.app_registry.list()
        assert apps['total'] == 2
        assert 'app1' in apps['apps']
        assert 'app2' not in apps['apps']
        assert 'app3' in apps['apps']

    def test_singleton_get_publisher(self, tmp_path, monkeypatch):
        """Should get singleton publisher instance."""
        from smartpublisher.publisher import get_publisher, _default_publisher

        # Reset singleton for test
        import smartpublisher.publisher
        smartpublisher.publisher._default_publisher = None

        # Get first instance
        pub1 = get_publisher()
        assert pub1 is not None

        # Get second instance (should be same)
        pub2 = get_publisher()
        assert pub2 is pub1
