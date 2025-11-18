"""
CLIChannel - CLI channel implementation.

Key principle: Use ONLY SmartSwitch APIs!
- switcher.describe() → auto-generated help
- switcher.get(method) → callable (handles validation)
- NO custom parsing, NO inspect, NO validation
- SmartSwitch does EVERYTHING
"""

import json
import sys
from typing import List, Tuple
from smartroute.core import Router, route, RoutedClass

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


class CLIChannel(RoutedClass):
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

    @route("cli_api")
    def help(self, handler_name: str = None) -> dict:
        """
        Show help - auto-generated from SmartSwitch.

        Args:
            handler_name: Optional handler name

        Returns:
            dict: Help data from switcher.describe()
        """
        if handler_name:
            instance = self.publisher.get_handler(handler_name)
            if instance is None:
                return {"error": f"Handler '{handler_name}' not found"}
            if hasattr(instance, 'api'):
                return instance.api.describe()
            return {"error": f"Handler '{handler_name}' has no API"}

        # General help - use SmartSwitch API
        return self.publisher.api.describe()

    @route("cli_api")
    def version(self) -> dict:
        """Show version information."""
        return {
            "app": self.publisher.__class__.__name__,
            "smartpublisher": "0.3.0",
            "smartswitch": "0.11.0"
        }

    def run(self, args: list = None):
        """
        Run CLI - orchestrates command dispatch to specialized handlers.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])
        """
        if args is None:
            args = sys.argv[1:]

        if args and args[0] == '--complete':
            self._handle_completion(args[1:])
            return

        # Show help cases
        if not args or args[0] in ['--help', '-h']:
            self._show_general_help()
            return

        if len(args) == 1:
            self._show_handler_help(args[0])
            return

        # Parse and route
        handler_name = args[0]
        method_name = args[1] if len(args) > 1 else None
        method_args = args[2:]

        if handler_name == '_system':
            self._handle_system_command(method_name, method_args)
        else:
            self._handle_business_command(handler_name, method_name, method_args)

    def _show_general_help(self):
        """Show general help from Publisher API."""
        schema = self.publisher.api.describe()
        output = self.formatter.format_help(schema)
        print(output)

    def _show_handler_help(self, handler_name: str):
        """Show help for specific handler."""
        instance = self.publisher.get_handler(handler_name)
        if instance and hasattr(instance, 'api'):
            schema = instance.api.describe()
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Handler not found or no API - delegate to business command handler
        self._handle_business_command(handler_name, None, [])

    def _handle_system_command(self, method_name: str, method_args: list):
        """
        Handle _system commands.

        Args:
            method_name: System command to execute (None = show help)
            method_args: Arguments for the command
        """
        if not method_name:
            system_meta = self.publisher.handler_members().get('_system')
            schema = system_meta['router'].describe() if system_meta else {}
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Execute system command - SmartSwitch handles everything
        try:
            system_handler = self.publisher.get_handler('_system')
            method_callable = system_handler.api.get(method_name, use_smartasync=True)
            result = method_callable(system_handler)
            output = self.formatter.format_json(result)
            print(output)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    # ------------------------------------------------------------------ #
    # Completion handling
    # ------------------------------------------------------------------ #

    def _handle_completion(self, completion_args: list):
        """
        Handle dynamic completion requests.

        Args:
            completion_args: [shell, cursor?, tokens...]
        """
        if not completion_args:
            payload = {
                "error": "missing shell identifier",
                "suggestions": []
            }
            print(json.dumps(payload))
            return

        shell = completion_args[0]
        cursor = None
        tokens_start = 1

        if len(completion_args) > 1 and completion_args[1].isdigit():
            cursor = int(completion_args[1])
            tokens_start = 2

        tokens = completion_args[tokens_start:]
        payload = self._generate_completion_payload(shell, cursor, tokens)
        print(json.dumps(payload))

    def _generate_completion_payload(self, shell: str, cursor: int | None, tokens: List[str]) -> dict:
        """
        Build completion suggestions based on current tokens.

        Args:
            shell: Shell requesting suggestions
            cursor: Cursor position (optional)
            tokens: Tokenized command line without program name

        Returns:
            dict: Completion payload
        """
        completed_tokens, current_fragment = self._split_tokens(tokens)

        try:
            suggestions = self._suggest_for_context(completed_tokens, current_fragment)
        except Exception as exc:
            suggestions = []
            error = str(exc)
        else:
            error = None

        payload = {
            "shell": shell,
            "cursor": cursor,
            "current_fragment": current_fragment,
            "completed_tokens": completed_tokens,
            "suggestions": suggestions,
        }

        if error:
            payload["error"] = error

        return payload

    @staticmethod
    def _split_tokens(tokens: List[str]) -> Tuple[List[str], str]:
        """
        Split tokens into fully completed parts and the current fragment.
        """
        if not tokens:
            return [], ""

        if tokens[-1] == "":
            return tokens[:-1], ""
        return tokens[:-1], tokens[-1]

    def _suggest_for_context(self, completed_tokens: List[str], fragment: str) -> List[dict]:
        """
        Return suggestions based on depth.
        """
        depth = len(completed_tokens)

        if depth == 0:
            return self._suggest_handlers(fragment)

        handler_name = completed_tokens[0]

        if handler_name == '_system':
            if depth == 1:
                return self._suggest_system_methods(fragment)
            if depth >= 2:
                return self._suggest_parameters('_system', completed_tokens[1], fragment)
            return []

        if depth == 1:
            return self._suggest_methods(handler_name, fragment)

        if depth >= 2:
            method_name = completed_tokens[1]
            return self._suggest_parameters(handler_name, method_name, fragment)

        return []

    def _suggest_handlers(self, fragment: str) -> List[dict]:
        """Suggest handler names."""
        fragment_lower = fragment.lower()
        suggestions = []

        handlers = self.publisher.get_handlers()

        for name, instance in sorted(handlers.items()):
            if fragment and not name.lower().startswith(fragment_lower):
                continue

            description = getattr(instance.__class__, '__doc__', '') or ''
            suggestions.append({
                "type": "handler",
                "value": name,
                "display": name,
                "description": description.strip(),
                "inline_hint": "",
            })

        return suggestions

    def _suggest_methods(self, handler_name: str, fragment: str) -> List[dict]:
        """Suggest methods for a handler."""
        handler = self.publisher.get_handler(handler_name)
        if not handler or not hasattr(handler, 'api'):
            return []

        schema = handler.api.describe()
        methods = schema.get('methods', {})
        fragment_lower = fragment.lower()
        suggestions = []

        for method_name, info in methods.items():
            if fragment and not method_name.lower().startswith(fragment_lower):
                continue

            raw_params = info.get('parameters', {})
            param_defs = []
            if isinstance(raw_params, dict):
                for pname, pdata in raw_params.items():
                    pdata = pdata or {}
                    pdata.setdefault('name', pname)
                    param_defs.append(pdata)
            elif isinstance(raw_params, list):
                param_defs = raw_params
            else:
                param_defs = []

            inline_hint = " ".join(
                f"<{param['name']}>" if param.get('required') else f"[{param['name']}]"
                for param in param_defs
            )

            suggestions.append({
                "type": "method",
                "value": method_name,
                "display": method_name,
                "description": info.get('description', ''),
                "inline_hint": inline_hint,
            })

        return suggestions

    def _suggest_system_methods(self, fragment: str) -> List[dict]:
        """Suggest methods under the _system handler."""
        if '_system' not in self.publisher.list_handlers():
            return []

        system_handler = self.publisher.get_handler('_system')
        schema = system_handler.api.describe()
        methods = schema.get('methods', {})
        fragment_lower = fragment.lower()
        suggestions = []

        for method_name, info in methods.items():
            if fragment and not method_name.lower().startswith(fragment_lower):
                continue

            suggestions.append({
                "type": "system",
                "value": method_name,
                "display": method_name,
                "description": info.get('description', ''),
                "inline_hint": "",
            })

        return suggestions

    def _suggest_parameters(self, handler_name: str, method_name: str, fragment: str) -> List[dict]:
        """Suggest parameters for a specific method."""
        handler = self.publisher.get_handler(handler_name)
        if not handler or not hasattr(handler, 'api'):
            return []

        schema = handler.api.describe()
        methods = schema.get('methods', {})
        method_schema = methods.get(method_name)

        if not method_schema:
            return []

        raw_params = method_schema.get('parameters', {})
        if isinstance(raw_params, dict):
            params = []
            for pname, pdata in raw_params.items():
                pdata = pdata or {}
                pdata.setdefault('name', pname)
                params.append(pdata)
        elif isinstance(raw_params, list):
            params = raw_params
        else:
            params = []
        fragment_lower = fragment.lower()
        suggestions = []

        for param in params:
            name = param.get('name', '')
            if fragment and not name.lower().startswith(fragment_lower):
                continue

            param_type = param.get('type', 'any')
            hint = f"<{param_type}>"
            description = param.get('description') or f"{'required' if param.get('required') else 'optional'} parameter"

            suggestions.append({
                "type": "parameter",
                "value": name,
                "display": name,
                "description": description,
                "inline_hint": hint,
                "required": param.get('required', False),
            })

        return suggestions

    def _handle_business_command(self, handler_name: str, method_name: str, method_args: list):
        """
        Handle business logic commands.

        Args:
            handler_name: Name of the handler to invoke
            method_name: Method to execute (None = show help)
            method_args: Arguments for the method
        """
        handlers = self.publisher.get_handlers()
        if handler_name not in handlers:
            print(f"Error: Handler '{handler_name}' not found")
            print(f"Available: {', '.join(self.publisher.list_handlers())}")
            return

        instance = handlers[handler_name]

        # Check has API
        if not hasattr(instance, 'api'):
            print(f"Error: Handler '{handler_name}' has no API")
            return

        # No method: show handler help
        if not method_name:
            schema = instance.api.describe()
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Execute method - SmartSwitch handles EVERYTHING
        try:
            method_callable = instance.api.get(method_name, use_smartasync=True)
            result = method_callable(instance)
            output = self.formatter.format_json(result)
            print(output)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
