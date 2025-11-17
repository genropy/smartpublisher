"""Tests for app registry."""

import pytest

from smartpublisher.registry import AppRegistry, get_local_registry, get_global_registry


class TestAppRegistry:
    """Test AppRegistry functionality."""

    def test_init(self, tmp_path):
        """Should initialize registry with file path."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        assert registry.registry_path == registry_file
        # Registry data should be initialized
        assert isinstance(registry._data, dict)

    def test_registry_file_creation(self, tmp_path):
        """Should create registry file on save."""
        registry_file = tmp_path / "test_registry" / "apps.json"
        registry = AppRegistry(registry_file)

        # Add an app to trigger save
        registry.add("test_app", str(tmp_path), "main", "App")

        # File should now exist
        assert registry_file.exists()
        assert registry_file.parent.exists()

    def test_add_app(self, tmp_path):
        """Should register app metadata."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        # Create test directory
        app_path = tmp_path / "test_app"
        app_path.mkdir()

        result = registry.add("test_app", str(app_path), "main", "TestApp")

        assert result["status"] == "registered"
        assert result["name"] == "test_app"
        assert result["module"] == "main"
        assert result["class"] == "TestApp"

    def test_add_app_nonexistent_path(self, tmp_path):
        """Should reject nonexistent path."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        nonexistent = tmp_path / "does_not_exist"
        result = registry.add("test_app", str(nonexistent))

        assert "error" in result
        assert "does not exist" in result["error"].lower()

    def test_remove_app(self, tmp_path):
        """Should unregister app."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        # Add app first
        app_path = tmp_path / "test_app"
        app_path.mkdir()
        registry.add("test_app", str(app_path))

        # Remove it
        result = registry.remove("test_app")

        assert result["status"] == "removed"
        assert result["name"] == "test_app"

    def test_remove_app_not_found(self, tmp_path):
        """Should handle removing nonexistent app."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        result = registry.remove("nonexistent")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_list_apps_empty(self, tmp_path):
        """Should return empty list when no apps registered."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        apps = registry.list()

        assert isinstance(apps, dict)
        assert apps["total"] == 0
        assert apps["apps"] == {}

    def test_list_apps_with_data(self, tmp_path):
        """Should list registered apps."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        # Add apps
        app1_path = tmp_path / "app1"
        app1_path.mkdir()
        app2_path = tmp_path / "app2"
        app2_path.mkdir()

        registry.add("app1", str(app1_path))
        registry.add("app2", str(app2_path))

        apps = registry.list()

        assert apps["total"] == 2
        assert "app1" in apps["apps"]
        assert "app2" in apps["apps"]

    def test_getapp(self, tmp_path):
        """Should get app info."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        # Add app
        app_path = tmp_path / "test_app"
        app_path.mkdir()
        registry.add("test_app", str(app_path), "main", "TestApp")

        # Get info
        info = registry.getapp("test_app")

        assert info["name"] == "test_app"
        assert info["module"] == "main"
        assert info["class"] == "TestApp"

    def test_getapp_not_found(self, tmp_path):
        """Should handle getting nonexistent app."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        info = registry.getapp("nonexistent")

        assert "error" in info
        assert "not found" in info["error"].lower()

    def test_load_app_not_found(self, tmp_path):
        """Should raise error for nonexistent app."""
        registry_file = tmp_path / "apps.json"
        registry = AppRegistry(registry_file)

        with pytest.raises(ValueError, match="not found"):
            registry.load("nonexistent")

    def test_registry_persistence(self, tmp_path):
        """Should persist data across instances."""
        registry_file = tmp_path / "apps.json"

        # Create first instance and add app
        registry1 = AppRegistry(registry_file)
        app_path = tmp_path / "test_app"
        app_path.mkdir()
        registry1.add("test_app", str(app_path))

        # Create second instance
        registry2 = AppRegistry(registry_file)

        # Should load existing data
        apps = registry2.list()
        assert apps["total"] == 1
        assert "test_app" in apps["apps"]


class TestGetLocalRegistry:
    """Test get_local_registry function."""

    def test_returns_app_registry(self):
        """Should return AppRegistry instance."""
        registry = get_local_registry()

        assert isinstance(registry, AppRegistry)

    def test_uses_local_path(self):
        """Should use local .published file."""
        registry = get_local_registry()

        # Path should end with .published
        assert registry.registry_path.name == ".published"


class TestGetGlobalRegistry:
    """Test get_global_registry function."""

    def test_returns_app_registry(self):
        """Should return AppRegistry instance."""
        registry = get_global_registry()

        assert isinstance(registry, AppRegistry)

    def test_uses_home_path(self):
        """Should use home directory path."""
        registry = get_global_registry()

        # Should contain .smartlibs and registry.json in path
        path_str = str(registry.registry_path)
        assert ".smartlibs" in path_str
        assert "registry.json" in path_str
