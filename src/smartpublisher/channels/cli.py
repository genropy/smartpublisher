"""
PublisherCLI - CLI channel implementation.

Key principle: Use ONLY SmartSwitch APIs!
- switcher.describe() → auto-generated help
- switcher.get(method) → callable (handles validation)
- NO custom parsing, NO inspect, NO validation
- SmartSwitch does EVERYTHING
"""

import sys
from smartroute.core import Router

# Try relative import first (when used as package)
# Fall back to absolute import (when run directly)
try:
    from ..output_formatter import OutputFormatter
except ImportError:
    import os
    import sys
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from output_formatter import OutputFormatter


class PublisherCLI:
    """
    CLI channel for Publisher.

    Uses ONLY SmartSwitch APIs - no custom code.
    SmartSwitch handles: validation, introspection, execution.
    """

    # CLI-specific utility commands
    cli_api = Router(name="cli")

    def __init__(self, publisher):
        """Initialize CLI channel."""
        self.publisher = publisher
        self.formatter = OutputFormatter()

    @cli_api
    def help(self, handler_name: str = None) -> dict:
        """
        Show help - auto-generated from SmartSwitch.

        Args:
            handler_name: Optional handler name

        Returns:
            dict: Help data from switcher.describe()
        """
        if handler_name:
            # Get help for specific handler
            if handler_name in self.publisher.published_instances:
                instance = self.publisher.published_instances[handler_name]
                if hasattr(instance.__class__, 'api'):
                    # SmartSwitch provides complete schema
                    return instance.__class__.api.describe()
                return {"error": f"Handler '{handler_name}' has no API"}
            return {"error": f"Handler '{handler_name}' not found"}

        # General help - use SmartSwitch API
        return self.publisher.api.describe()

    @cli_api
    def version(self) -> dict:
        """Show version information."""
        return {
            "app": self.publisher.__class__.__name__,
            "smartpublisher": "0.3.0",
            "smartswitch": "0.11.0"
        }

    def run(self, args: list = None):
        """
        Run CLI using ONLY SmartSwitch APIs.

        SmartSwitch handles ALL the work:
        - Argument parsing
        - Validation
        - Type conversion
        - Execution

        We just dispatch and format output.
        """
        if args is None:
            args = sys.argv[1:]

        # No args? Show help from SmartSwitch
        if not args or args[0] in ['--help', '-h']:
            # Get schema from SmartSwitch
            schema = self.publisher.api.describe()
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Single arg = handler name, show handler help
        if len(args) == 1:
            handler_name = args[0]
            if handler_name in self.publisher.published_instances:
                instance = self.publisher.published_instances[handler_name]
                if hasattr(instance.__class__, 'api'):
                    # SmartSwitch provides schema
                    schema = instance.__class__.api.describe()
                    output = self.formatter.format_help(schema)
                    print(output)
                    return

        # Parse: handler_name method_name [args...]
        handler_name = args[0]
        method_name = args[1] if len(args) > 1 else None

        # Special case: system commands
        if handler_name == '_system':
            if not method_name:
                # Show system commands
                schema = self.publisher.api['_system'].__class__.api.describe()
                output = self.formatter.format_help(schema)
                print(output)
                return

            # Execute system command - SmartSwitch handles everything
            try:
                # Get callable from SmartSwitch
                system_handler = self.publisher.published_instances['_system']
                method_callable = system_handler.__class__.api.get(method_name, use_smartasync=True)

                # Call with instance - SmartSwitch validates args
                result = method_callable(system_handler)

                # Format and print
                output = self.formatter.format_json(result)
                print(output)
                return

            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        # Business command
        if handler_name not in self.publisher.published_instances:
            print(f"Error: Handler '{handler_name}' not found")
            print(f"Available: {', '.join(self.publisher.published_instances.keys())}")
            return

        instance = self.publisher.published_instances[handler_name]

        if not hasattr(instance.__class__, 'api'):
            print(f"Error: Handler '{handler_name}' has no API")
            return

        if not method_name:
            # Show handler help
            schema = instance.__class__.api.describe()
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Execute method - SmartSwitch handles EVERYTHING
        try:
            # Get callable from SmartSwitch
            method_callable = instance.__class__.api.get(method_name, use_smartasync=True)

            # Call with instance
            # SmartSwitch handles:
            # - Parsing args[2:]
            # - Validation
            # - Type conversion
            # - Execution
            result = method_callable(instance)

            # Format and print at edge
            output = self.formatter.format_json(result)
            print(output)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
