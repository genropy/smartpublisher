"""Tests for CLI module (registry management and entry point)."""

import sys
import json
import pytest
from unittest.mock import patch
from smartpublisher import cli


class TestLoadRegistry:
    """Test load_registry function."""

    def test_load_existing_registry(self, tmp_path):
        """Test loading existing registry."""
        registry_file = tmp_path / "registry.json"
        test_data = {"apps": {"test_app": {"path": "/test/path"}}}
        registry_file.write_text(json.dumps(test_data))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            result = cli.load_registry()

        assert result == test_data

    def test_load_nonexistent_registry(self, tmp_path):
        """Test loading non-existent registry returns empty structure."""
        registry_file = tmp_path / "nonexistent.json"

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            result = cli.load_registry()

        assert result == {"apps": {}}

    def test_load_global_registry(self, tmp_path):
        """Test loading global registry."""
        global_registry = tmp_path / "global.json"
        test_data = {"apps": {"global_app": {"path": "/global/path"}}}
        global_registry.write_text(json.dumps(test_data))

        with patch.object(cli, "GLOBAL_REGISTRY", global_registry):
            result = cli.load_registry(global_mode=True)

        assert result == test_data


class TestSaveRegistry:
    """Test save_registry function."""

    def test_save_registry_creates_file(self, tmp_path):
        """Test saving registry creates file."""
        registry_file = tmp_path / "registry.json"
        test_data = {"apps": {"test_app": {"path": "/test/path"}}}

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            cli.save_registry(test_data)

        assert registry_file.exists()
        saved_data = json.loads(registry_file.read_text())
        assert saved_data == test_data

    def test_save_registry_creates_parent_dirs(self, tmp_path):
        """Test saving registry creates parent directories."""
        registry_file = tmp_path / "nested" / "dirs" / "registry.json"
        test_data = {"apps": {}}

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            cli.save_registry(test_data)

        assert registry_file.exists()
        assert registry_file.parent.exists()

    def test_save_global_registry(self, tmp_path):
        """Test saving to global registry."""
        global_registry = tmp_path / "global.json"
        test_data = {"apps": {"global_app": {"path": "/path"}}}

        with patch.object(cli, "GLOBAL_REGISTRY", global_registry):
            cli.save_registry(test_data, global_mode=True)

        assert global_registry.exists()
        saved_data = json.loads(global_registry.read_text())
        assert saved_data == test_data


class TestDiscoverPublisherClass:
    """Test discover_publisher_class function."""

    def test_discover_in_valid_directory(self, tmp_path):
        """Test discovering Publisher class in directory."""
        app_file = tmp_path / "myapp.py"
        app_file.write_text("""
from smartpublisher import Publisher

class MyApp(Publisher):
    pass
""")

        module_name, class_name = cli.discover_publisher_class(tmp_path)

        assert module_name == "myapp"
        assert class_name == "MyApp"

    def test_discover_not_a_directory(self, tmp_path):
        """Test with file instead of directory."""
        app_file = tmp_path / "notadir.py"
        app_file.write_text("content")

        module_name, class_name = cli.discover_publisher_class(app_file)

        assert module_name is None
        assert class_name is None

    def test_discover_no_publisher_class(self, tmp_path):
        """Test directory with no Publisher class."""
        other_file = tmp_path / "other.py"
        other_file.write_text("print('hello')")

        module_name, class_name = cli.discover_publisher_class(tmp_path)

        assert module_name is None
        assert class_name is None

    def test_discover_multiple_files(self, tmp_path):
        """Test directory with multiple files, finds Publisher."""
        (tmp_path / "other.py").write_text("x = 1")
        (tmp_path / "app.py").write_text("""
class MainApp(Publisher):
    pass
""")

        module_name, class_name = cli.discover_publisher_class(tmp_path)

        assert module_name == "app"
        assert class_name == "MainApp"

    def test_discover_ignores_private_files(self, tmp_path):
        """Test that private files are ignored."""
        (tmp_path / "_private.py").write_text("class MyApp(Publisher): pass")
        (tmp_path / "__init__.py").write_text("class MyApp(Publisher): pass")

        module_name, class_name = cli.discover_publisher_class(tmp_path)

        assert module_name is None
        assert class_name is None


class TestAddApp:
    """Test add_app function."""

    def test_add_app_success(self, tmp_path, capsys):
        """Test successfully adding an app."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("class MyApp(Publisher): pass")

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            cli.add_app("testapp", path=str(app_dir))

        # Check registry was saved
        assert registry_file.exists()
        registry = json.loads(registry_file.read_text())
        assert "testapp" in registry["apps"]
        assert registry["apps"]["testapp"]["module"] == "main"
        assert registry["apps"]["testapp"]["class"] == "MyApp"

        # Check output
        captured = capsys.readouterr()
        assert "testapp" in captured.out
        assert "registered" in captured.out

    def test_add_app_nonexistent_path(self, tmp_path, capsys):
        """Test adding app with non-existent path."""
        registry_file = tmp_path / "registry.json"
        fake_path = tmp_path / "nonexistent"

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with pytest.raises(SystemExit) as exc:
                cli.add_app("testapp", path=str(fake_path))

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.out

    def test_add_app_no_publisher_found(self, tmp_path, capsys):
        """Test adding app when no Publisher class found."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "other.py").write_text("print('hello')")

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with pytest.raises(SystemExit) as exc:
                cli.add_app("testapp", path=str(app_dir))

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "No Publisher class found" in captured.out

    def test_add_app_default_path(self, tmp_path, capsys):
        """Test adding app with default path (current directory)."""
        import os

        registry_file = tmp_path / "registry.json"
        (tmp_path / "app.py").write_text("class App(Publisher): pass")

        # Change to tmp_path directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.object(cli, "LOCAL_REGISTRY", registry_file):
                cli.add_app("testapp")
        finally:
            os.chdir(old_cwd)

        registry = json.loads(registry_file.read_text())
        assert "testapp" in registry["apps"]

    def test_add_app_global_mode(self, tmp_path, capsys):
        """Test adding app in global mode."""
        global_registry = tmp_path / "global.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("class MyApp(Publisher): pass")

        with patch.object(cli, "GLOBAL_REGISTRY", global_registry):
            cli.add_app("testapp", path=str(app_dir), global_mode=True)

        registry = json.loads(global_registry.read_text())
        assert "testapp" in registry["apps"]

        captured = capsys.readouterr()
        assert "globally" in captured.out


class TestListApps:
    """Test list_apps function."""

    def test_list_empty_registry(self, tmp_path, capsys):
        """Test listing when no apps registered."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps({"apps": {}}))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            cli.list_apps()

        captured = capsys.readouterr()
        assert "No apps registered" in captured.out

    def test_list_apps_local(self, tmp_path, capsys):
        """Test listing local apps."""
        registry_file = tmp_path / "registry.json"
        test_data = {
            "apps": {
                "app1": {"path": "/path/to/app1"},
                "app2": {"path": "/path/to/app2"},
            }
        }
        registry_file.write_text(json.dumps(test_data))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            cli.list_apps()

        captured = capsys.readouterr()
        assert "app1" in captured.out
        assert "app2" in captured.out
        assert "/path/to/app1" in captured.out
        assert "/path/to/app2" in captured.out

    def test_list_apps_global(self, tmp_path, capsys):
        """Test listing global apps."""
        global_registry = tmp_path / "global.json"
        test_data = {"apps": {"global_app": {"path": "/global/path"}}}
        global_registry.write_text(json.dumps(test_data))

        with patch.object(cli, "GLOBAL_REGISTRY", global_registry):
            cli.list_apps(global_mode=True)

        captured = capsys.readouterr()
        assert "Global" in captured.out
        assert "global_app" in captured.out


class TestRemoveApp:
    """Test remove_app function."""

    def test_remove_existing_app(self, tmp_path, capsys):
        """Test removing existing app."""
        registry_file = tmp_path / "registry.json"
        test_data = {
            "apps": {
                "app1": {"path": "/path1"},
                "app2": {"path": "/path2"},
            }
        }
        registry_file.write_text(json.dumps(test_data))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            cli.remove_app("app1")

        # Check app was removed
        registry = json.loads(registry_file.read_text())
        assert "app1" not in registry["apps"]
        assert "app2" in registry["apps"]

        captured = capsys.readouterr()
        assert "removed" in captured.out

    def test_remove_nonexistent_app(self, tmp_path, capsys):
        """Test removing non-existent app."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps({"apps": {}}))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with pytest.raises(SystemExit) as exc:
                cli.remove_app("nonexistent")

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestLoadApp:
    """Test load_app function."""

    def test_load_app_success(self, tmp_path):
        """Test successfully loading an app."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()

        # Create a simple Publisher class
        app_file = app_dir / "main.py"
        app_file.write_text("""
from smartpublisher import Publisher

class MyApp(Publisher):
    def initialize(self):
        pass
""")

        test_data = {
            "apps": {
                "testapp": {
                    "path": str(app_dir),
                    "module": "main",
                    "class": "MyApp",
                }
            }
        }
        registry_file.write_text(json.dumps(test_data))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            app = cli.load_app("testapp")

        assert app is not None
        assert app.__class__.__name__ == "MyApp"

    def test_load_app_not_found(self, tmp_path, capsys):
        """Test loading non-existent app."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps({"apps": {}}))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with patch.object(cli, "GLOBAL_REGISTRY", registry_file):
                with pytest.raises(SystemExit) as exc:
                    cli.load_app("nonexistent")

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_load_app_import_error(self, tmp_path, capsys):
        """Test loading app with import error."""
        registry_file = tmp_path / "registry.json"
        test_data = {
            "apps": {
                "testapp": {
                    "path": "/nonexistent/path",
                    "module": "nonexistent",
                    "class": "NonExistent",
                }
            }
        }
        registry_file.write_text(json.dumps(test_data))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with pytest.raises(SystemExit) as exc:
                cli.load_app("testapp")

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Error loading app" in captured.out


class TestPrintHelp:
    """Test print_help function."""

    def test_print_help(self, capsys):
        """Test that help is printed."""
        cli.print_help()

        captured = capsys.readouterr()
        assert "smpub" in captured.out
        assert "add" in captured.out
        assert "remove" in captured.out
        assert "list" in captured.out
        assert "serve" in captured.out


class TestMain:
    """Test main entry point."""

    def test_main_no_args(self, capsys):
        """Test main with no arguments shows help."""
        with patch.object(sys, "argv", ["smpub"]):
            cli.main()

        captured = capsys.readouterr()
        assert "smpub" in captured.out
        assert "add" in captured.out

    def test_main_help_flag(self, capsys):
        """Test main with --help flag."""
        with patch.object(sys, "argv", ["smpub", "--help"]):
            cli.main()

        captured = capsys.readouterr()
        assert "smpub" in captured.out

    def test_main_add_command(self, tmp_path, capsys):
        """Test main with add command."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("class MyApp(Publisher): pass")

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with patch.object(sys, "argv", ["smpub", "add", "testapp", "--path", str(app_dir)]):
                cli.main()

        registry = json.loads(registry_file.read_text())
        assert "testapp" in registry["apps"]

    def test_main_list_command(self, tmp_path, capsys):
        """Test main with list command."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps({"apps": {}}))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with patch.object(sys, "argv", ["smpub", "list"]):
                cli.main()

        captured = capsys.readouterr()
        assert "No apps registered" in captured.out

    def test_main_remove_command(self, tmp_path, capsys):
        """Test main with remove command."""
        registry_file = tmp_path / "registry.json"
        test_data = {"apps": {"testapp": {"path": "/path"}}}
        registry_file.write_text(json.dumps(test_data))

        with patch.object(cli, "LOCAL_REGISTRY", registry_file):
            with patch.object(sys, "argv", ["smpub", "remove", "testapp"]):
                cli.main()

        registry = json.loads(registry_file.read_text())
        assert "testapp" not in registry["apps"]

    def test_main_serve_default_port(self, tmp_path):
        """Test main with serve command (default port)."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("""
from smartpublisher import Publisher

class MyApp(Publisher):
    def initialize(self):
        pass

    def run(self, mode=None, port=None):
        # Verify parameters without calling super().run()
        assert mode == "http"
        assert port == 8000
        # Don't call super().run() to avoid starting real server
""")

        test_data = {
            "apps": {
                "testapp": {
                    "path": str(app_dir),
                    "module": "main",
                    "class": "MyApp",
                }
            }
        }
        registry_file.write_text(json.dumps(test_data))

        # Cleanup module cache after test
        if "main" in sys.modules:
            del sys.modules["main"]

        try:
            with patch.object(cli, "LOCAL_REGISTRY", registry_file):
                with patch.object(sys, "argv", ["smpub", "testapp", "serve"]):
                    cli.main()
        finally:
            # Always cleanup
            if "main" in sys.modules:
                del sys.modules["main"]

    def test_main_serve_custom_port(self, tmp_path):
        """Test main with serve command (custom port)."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("""
from smartpublisher import Publisher

class MyApp(Publisher):
    def initialize(self):
        pass

    def run(self, mode=None, port=None):
        # Verify parameters without calling super().run()
        assert mode == "http"
        assert port == 9000
        # Don't call super().run() to avoid starting real server
""")

        test_data = {
            "apps": {
                "testapp": {
                    "path": str(app_dir),
                    "module": "main",
                    "class": "MyApp",
                }
            }
        }
        registry_file.write_text(json.dumps(test_data))

        # Cleanup module cache before test
        if "main" in sys.modules:
            del sys.modules["main"]

        try:
            with patch.object(cli, "LOCAL_REGISTRY", registry_file):
                with patch.object(sys, "argv", ["smpub", "testapp", "serve", "9000"]):
                    cli.main()
        finally:
            # Always cleanup
            if "main" in sys.modules:
                del sys.modules["main"]

    def test_main_cli_mode(self, tmp_path):
        """Test main in CLI mode."""
        registry_file = tmp_path / "registry.json"
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("""
from smartpublisher import Publisher

class MyApp(Publisher):
    def initialize(self):
        pass

    def run(self, mode=None):
        # Verify parameters without calling super().run()
        assert mode == "cli"
        # Don't call super().run() to avoid running real CLI
""")

        test_data = {
            "apps": {
                "testapp": {
                    "path": str(app_dir),
                    "module": "main",
                    "class": "MyApp",
                }
            }
        }
        registry_file.write_text(json.dumps(test_data))

        # Cleanup module cache before test
        if "main" in sys.modules:
            del sys.modules["main"]

        try:
            with patch.object(cli, "LOCAL_REGISTRY", registry_file):
                with patch.object(sys, "argv", ["smpub", "testapp", "handler", "method"]):
                    cli.main()
        finally:
            # Always cleanup
            if "main" in sys.modules:
                del sys.modules["main"]
