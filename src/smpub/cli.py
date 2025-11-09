"""
CLI entry point for smpub command.

Manages app registry and dispatches commands to published apps.
"""

import sys
import json
import importlib
from pathlib import Path


# Registry file locations
LOCAL_REGISTRY = Path.cwd() / ".published"
GLOBAL_REGISTRY = Path.home() / ".smartlibs" / "publisher" / "registry.json"


def load_registry(global_mode=False):
    """Load app registry from file."""
    registry_path = GLOBAL_REGISTRY if global_mode else LOCAL_REGISTRY

    if not registry_path.exists():
        return {"apps": {}}

    with open(registry_path) as f:
        return json.load(f)


def save_registry(registry, global_mode=False):
    """Save app registry to file."""
    registry_path = GLOBAL_REGISTRY if global_mode else LOCAL_REGISTRY

    # Create parent directory if needed
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)


def add_app(name, path, global_mode=False):
    """Register an app in registry."""
    registry = load_registry(global_mode)

    path = Path(path).resolve()
    if not path.exists():
        print(f"Error: Path {path} does not exist")
        sys.exit(1)

    registry["apps"][name] = {
        "path": str(path),
        "module": f"{name}.main",  # Convention
        "class": "MainClass"        # Convention
    }

    save_registry(registry, global_mode)
    mode_str = "globally" if global_mode else "locally"
    print(f"✓ App '{name}' registered {mode_str} at {path}")


def list_apps(global_mode=False):
    """List all registered apps."""
    registry = load_registry(global_mode)

    if not registry["apps"]:
        mode_str = "globally" if global_mode else "in this directory"
        print(f"No apps registered {mode_str}.")
        print(f"Use 'smpub add <name> --path <path>' to add one.")
        return

    mode_str = "Global" if global_mode else "Local"
    print(f"{mode_str} registered apps:")
    for name, info in registry["apps"].items():
        print(f"  {name} → {info['path']}")


def remove_app(name, global_mode=False):
    """Remove app from registry."""
    registry = load_registry(global_mode)

    if name in registry["apps"]:
        del registry["apps"][name]
        save_registry(registry, global_mode)
        mode_str = "globally" if global_mode else "locally"
        print(f"✓ App '{name}' removed {mode_str}")
    else:
        mode_str = "global" if global_mode else "local"
        print(f"Error: App '{name}' not found in {mode_str} registry")
        sys.exit(1)


def load_app(name, global_mode=False):
    """Load an app from registry."""
    registry = load_registry(global_mode)

    if name not in registry["apps"]:
        # Try the other registry
        other_global = not global_mode
        registry = load_registry(other_global)
        if name not in registry["apps"]:
            print(f"Error: App '{name}' not found in registry")
            print(f"Use 'smpub add {name} --path <path>' to register it")
            sys.exit(1)

    app_info = registry["apps"][name]
    app_path = Path(app_info["path"])

    # Add to sys.path
    sys.path.insert(0, str(app_path))

    # Import module
    try:
        mod = importlib.import_module(app_info["module"])
        app_class = getattr(mod, app_info["class"])
        return app_class()
    except (ImportError, AttributeError) as e:
        print(f"Error loading app '{name}': {e}")
        sys.exit(1)


def print_help():
    """Print CLI help."""
    print("""
smpub - Smart Publisher CLI

Management:
    smpub add <name> --path <path> [--global]
                                Register an app
    smpub remove <name> [--global]
                                Unregister an app
    smpub list [--global]       List registered apps

Execution:
    smpub <app-name> [command] [args...]
                                Run app command
    smpub <app-name> --help     Show app help

Examples:
    smpub add myapp --path ~/projects/myapp
    smpub myapp --help
    smpub myapp handler add key value
    smpub list
    smpub remove myapp

Options:
    --global                    Use global registry (~/.smartlibs/publisher/)
                                instead of local (./.published)
    """)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]
    global_mode = '--global' in sys.argv

    # Management commands
    if command == "add":
        if len(sys.argv) < 4 or '--path' not in sys.argv:
            print("Usage: smpub add <name> --path <path> [--global]")
            sys.exit(1)
        name = sys.argv[2]
        path_idx = sys.argv.index('--path') + 1
        if path_idx >= len(sys.argv):
            print("Error: --path requires a value")
            sys.exit(1)
        path = sys.argv[path_idx]
        add_app(name, path, global_mode)
        return

    if command == "list":
        list_apps(global_mode)
        return

    if command == "remove":
        if len(sys.argv) < 3:
            print("Usage: smpub remove <name> [--global]")
            sys.exit(1)
        name = sys.argv[2]
        remove_app(name, global_mode)
        return

    if command == "--help" or command == "-h":
        print_help()
        return

    # App execution
    app_name = command
    app = load_app(app_name, global_mode)

    # Remove 'smpub', app_name, and --global from argv
    new_argv = [sys.argv[0]]
    for arg in sys.argv[2:]:
        if arg != '--global':
            new_argv.append(arg)
    sys.argv = new_argv

    # Run in CLI mode
    app.run(mode='cli')


if __name__ == "__main__":
    main()
