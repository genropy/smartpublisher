"""
CLI entry point for smpub command.

New architecture with .apps routing and bash completion support.

Key principles:
- Use ONLY SmartSwitch APIs
- System commands start with . (dot)
- App commands are shortcuts: smpub myapp ... = .apps getapp + execute
- Bash completion driven by Switcher.describe()
"""

import sys
import json

# Try relative imports first (when used as package)
# Fall back to absolute imports (when run directly)
try:
    from .registry import get_local_registry, get_global_registry, discover_app
    from .channels.cli import PublisherCLI
    from .channels.http import PublisherHTTP
except ImportError:
    from registry import get_local_registry, get_global_registry, discover_app
    from channels.cli import PublisherCLI
    from channels.http import PublisherHTTP


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

class OutputFormatter:
    """Format structured data for CLI output."""

    @staticmethod
    def format(data: dict) -> str:
        """
        Format dict for CLI display.

        Args:
            data: Structured data from SmartSwitch

        Returns:
            str: Formatted output
        """
        if "error" in data:
            return f"✗ Error: {data['error']}"

        if "status" in data:
            status = data["status"]
            if status == "registered":
                return f"✓ App '{data['name']}' registered\n  Path: {data['path']}"
            elif status == "removed":
                return f"✓ App '{data['name']}' removed"
            elif status == "published":
                methods = ", ".join(data.get("methods", []))
                return f"✓ Published '{data['name']}' ({data['handler_class']})\n  Methods: {methods}"

        # List apps
        if "apps" in data and "total" in data:
            if data["total"] == 0:
                return "No apps registered."
            lines = [f"Registered apps ({data['total']}):"]
            for name, info in data["apps"].items():
                lines.append(f"  {name} → {info['path']}")
            return "\n".join(lines)

        # Generic dict formatting
        return json.dumps(data, indent=2)


# ============================================================================
# BASH COMPLETION
# ============================================================================

def handle_completion(args: list):
    """
    Handle bash completion requests.

    Args:
        args: ['--complete', level, partial_args...]

    Output:
        Space-separated list of suggestions (printed to stdout)
    """
    try:
        level = int(args[1])
        partial_args = args[2:] if len(args) > 2 else []
    except (IndexError, ValueError):
        return

    suggestions = []

    # Level 0: System commands + app names
    if level == 0:
        system_cmds = ['.apps']  # Future: .config, .version, etc.
        suggestions.extend(system_cmds)

        # Add app names from both registries
        try:
            local_reg = get_local_registry()
            suggestions.extend(local_reg._data["apps"].keys())
        except Exception:
            pass

        try:
            global_reg = get_global_registry()
            suggestions.extend(global_reg._data["apps"].keys())
        except Exception:
            pass

    # Level 1: Methods of system handler OR handler names
    elif level == 1 and len(partial_args) > 0:
        first_arg = partial_args[0]

        if first_arg.startswith('.'):
            # System command: return methods
            system_handler = first_arg[1:]  # Remove dot

            if system_handler == 'apps':
                # Get methods from AppRegistry Switcher
                from registry import AppRegistry
                schema = AppRegistry.api.describe()
                suggestions = list(schema.get('methods', {}).keys())

        else:
            # App name: return handler names
            try:
                registry = discover_app(first_arg)
                app = registry.load(first_arg)
                suggestions = list(app.published_instances.keys())
            except Exception:
                pass

    # Level 2: Methods of app handler
    elif level == 2 and len(partial_args) >= 2:
        app_name = partial_args[0]
        handler_name = partial_args[1]

        try:
            registry = discover_app(app_name)
            app = registry.load(app_name)
            handler = app.published_instances.get(handler_name)
            if handler and hasattr(handler.__class__, 'api'):
                schema = handler.__class__.api.describe()
                suggestions = list(schema.get('methods', {}).keys())
        except Exception:
            pass

    # Print suggestions (space-separated)
    print(' '.join(suggestions))


# ============================================================================
# SYSTEM COMMANDS
# ============================================================================

def handle_system_command(system_handler: str, args: list, global_mode: bool = False):
    """
    Handle system commands (e.g., .apps).

    Args:
        system_handler: Handler name (e.g., "apps")
        args: Remaining CLI arguments
        global_mode: Use global registry
    """
    if system_handler == "apps":
        # Get appropriate registry
        if global_mode:
            registry = get_global_registry()
        else:
            registry = get_local_registry()

        # No command: show help
        if len(args) == 0:
            schema = registry.api.describe()
            print("Registry commands:")
            for method_name, method_info in schema.get('methods', {}).items():
                doc = method_info.get('description', 'No description')
                print(f"  {method_name}: {doc}")
            return

        # Get command
        command = args[0]
        command_args = args[1:]

        try:
            # Get method from Switcher (SmartSwitch handles validation!)
            method = registry.api.get(command)

            # Call with remaining args (SmartSwitch converts CLI args to kwargs)
            # For now, simple positional mapping
            # TODO: Use SmartSwitch CLI parsing when available
            if command == "add":
                if len(command_args) < 2:
                    print("Usage: smpub .apps add <name> <path> [module] [class_name]")
                    sys.exit(1)
                name = command_args[0]
                path = command_args[1]
                module = command_args[2] if len(command_args) > 2 else "main"
                class_name = command_args[3] if len(command_args) > 3 else "App"
                result = method(registry, name=name, path=path, module=module, class_name=class_name)

            elif command == "remove":
                if len(command_args) < 1:
                    print("Usage: smpub .apps remove <name>")
                    sys.exit(1)
                name = command_args[0]
                result = method(registry, name=name)

            elif command == "list":
                result = method(registry)

            elif command == "getapp":
                if len(command_args) < 1:
                    print("Usage: smpub .apps getapp <name>")
                    sys.exit(1)
                name = command_args[0]
                result = method(registry, name=name)

            else:
                print(f"Unknown command: {command}")
                sys.exit(1)

            # Format and print result
            output = OutputFormatter.format(result)
            print(output)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        print(f"Unknown system handler: .{system_handler}")
        sys.exit(1)


# ============================================================================
# APP COMMANDS
# ============================================================================

def handle_app_command(app_name: str, args: list):
    """
    Handle app commands.

    This is shorthand for: .apps getapp <app_name> + execute command

    Args:
        app_name: Name of the app
        args: Command and arguments
    """
    try:
        # Discover and load app
        registry = discover_app(app_name)
        app = registry.load(app_name)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # No command: show help
    if len(args) == 0:
        print(f"App: {app_name}")
        print(f"Class: {app.__class__.__name__}")
        print("\nHandlers:")
        for handler_name in app.published_instances.keys():
            print(f"  {handler_name}")
        return

    # Create CLI channel and execute
    cli = PublisherCLI(app)
    cli.run(args)


# ============================================================================
# SPECIAL COMMANDS
# ============================================================================

def handle_serve_command(app_name: str, port: int = 8000):
    """
    Start HTTP server for an app.

    Args:
        app_name: Name of the app
        port: Port to listen on
    """
    try:
        # Discover and load app
        registry = discover_app(app_name)
        app = registry.load(app_name)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Create HTTP channel and run
    http = PublisherHTTP(app)
    print(f"Starting {app_name} on http://0.0.0.0:{port}")
    print(f"Swagger UI: http://localhost:{port}/docs")
    print(f"Health: http://localhost:{port}/_http/health")
    http.run(port=port)


def print_help():
    """Print CLI help."""
    print("""
smpub - Smart Publisher CLI

System Commands (start with .):
    smpub .apps add <name> <path> [module] [class]
                                Register an app
    smpub .apps remove <name>   Unregister an app
    smpub .apps list            List registered apps
    smpub .apps getapp <name>   Get app info

App Commands (shorthand):
    smpub <app-name> [handler] [method] [args...]
                                Execute app command
    smpub serve <app-name> [--port PORT]
                                Start HTTP server

Flags:
    --global                    Use global registry (~/.smartlibs/publisher/)
    --complete <level> [args...]
                                Bash completion (internal use)

Examples:
    # Register app
    smpub .apps add myapp ~/projects/myapp main ShopApp

    # List apps
    smpub .apps list

    # Run commands (shorthand)
    smpub myapp shop list
    smpub myapp _system list_handlers

    # Start server
    smpub serve myapp
    smpub serve myapp --port 8080

Notes:
    - System commands start with . (dot)
    - App commands are shortcuts: smpub myapp = .apps getapp myapp
    - Use --global for global registry, local by default
    """)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """CLI entry point."""
    # No args: show help
    if len(sys.argv) < 2:
        print_help()
        return

    # Parse flags
    global_mode = "--global" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--global"]

    # Handle bash completion
    if "--complete" in args:
        handle_completion(args)
        return

    # Handle help
    if args[0] in ["--help", "-h", "help"]:
        print_help()
        return

    # Handle serve (special command)
    if args[0] == "serve":
        if len(args) < 2:
            print("Usage: smpub serve <app-name> [--port PORT]")
            sys.exit(1)

        app_name = args[1]
        port = 8000

        if "--port" in args:
            try:
                port_idx = args.index("--port") + 1
                port = int(args[port_idx])
            except (IndexError, ValueError):
                print("Error: Invalid port")
                sys.exit(1)

        handle_serve_command(app_name, port)
        return

    # Route based on first arg
    first_arg = args[0]

    if first_arg.startswith('.'):
        # System command
        system_handler = first_arg[1:]  # Remove leading dot
        remaining_args = args[1:]
        handle_system_command(system_handler, remaining_args, global_mode)

    else:
        # App command (shorthand)
        app_name = first_arg
        remaining_args = args[1:]
        handle_app_command(app_name, remaining_args)


if __name__ == "__main__":
    main()
