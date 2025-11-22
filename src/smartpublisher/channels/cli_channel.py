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
from smartroute.core import Router, route
from ._base_channel import BaseChannel

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


class CLIChannel(BaseChannel):
    """
    CLI channel for Publisher.

    Uses ONLY SmartSwitch APIs - no custom code.
    SmartSwitch handles: validation, introspection, execution.
    """

    CHANNEL_CODE = "CLI"
    CHANNEL_CODE = "CLI"

    def __init__(self, registry):
        """
        Initialize CLI channel.

        Args:
            registry: ChanRegistry instance
        """
        super().__init__(registry)
        self.cli_api = Router(self, name="cli")
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
            instance = self.publisher.get_handler(handler_name, channel=self.CHANNEL_CODE)
            if instance is None:
                return {"error": f"Handler '{handler_name}' not found"}
            if hasattr(instance, "api"):
                return instance.api.describe(channel=self.CHANNEL_CODE)
            return {"error": f"Handler '{handler_name}' has no API"}

        # General help - use SmartSwitch API
        return self.publisher.api.describe(channel=self.CHANNEL_CODE)

    @route("cli_api")
    def version(self) -> dict:
        """Show version information."""
        return {
            "app": self.publisher.__class__.__name__,
            "smartpublisher": "0.3.0",
            "smartswitch": "0.11.0",
        }

    def run(self, args: list = None):
        """
        Run CLI - orchestrates command dispatch to specialized handlers.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])
        """
        if args is None:
            args = sys.argv[1:]

        if args and args[0] == "--complete":
            self._handle_completion(args[1:])
            return

        # Show help cases
        if not args or args[0] in ["--help", "-h"]:
            self._show_general_help()
            return

        root_methods = self._get_root_methods()

        if args[0].startswith("/"):
            method_name = args[0]
            if method_name not in root_methods:
                print(f"Error: Unknown command '{method_name}'")
                print(f"Available: {', '.join(sorted(root_methods.keys()))}")
                return
            self._handle_root_command(method_name, args[1:])
            return

        if len(args) == 1:
            self._show_handler_help(args[0])
            return

        # Parse and route
        handler_name = args[0]
        method_name = args[1] if len(args) > 1 else None
        method_args = args[2:]

        if handler_name == "_system":
            self._handle_system_command(method_name, method_args)
        else:
            self._handle_business_command(handler_name, method_name, method_args)

    def _show_general_help(self):
        """Show general help from Publisher API."""
        schema = self.publisher.api.describe(channel=self.CHANNEL_CODE)
        output = self.formatter.format_help(schema)
        print(output)

    def _show_handler_help(self, handler_name: str):
        """Show help for specific handler."""
        if handler_name.startswith("/"):
            root_methods = self._get_root_methods()
            method_schema = root_methods.get(handler_name)
            if method_schema:
                output = self.formatter.format_help(
                    {"name": handler_name, "methods": {handler_name: method_schema}}
                )
                print(output)
                return

        instance = self.publisher.get_handler(handler_name, channel=self.CHANNEL_CODE)
        if instance and hasattr(instance, "api"):
            schema = instance.api.describe(channel=self.CHANNEL_CODE)
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
            system_meta = self.publisher.handler_members(channel=self.CHANNEL_CODE).get("_system")
            schema = (
                system_meta["router"].describe(channel=self.CHANNEL_CODE) if system_meta else {}
            )
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Execute system command - SmartSwitch handles everything
        try:
            system_handler = self.publisher.get_handler("_system", channel=self.CHANNEL_CODE)
            method_callable = system_handler.api.get(method_name, use_smartasync=True)
            positional, keyword = self._split_cli_args(method_args)
            # SmartSwitch returns a bound callable, so just forward parsed args
            result = method_callable(*positional, **keyword)
            output = self.formatter.format_json(result)
            print(output)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def _get_root_methods(self) -> dict:
        """Return publisher root methods that start with '/'."""
        schema = self.publisher.api.describe(channel=self.CHANNEL_CODE)
        methods = schema.get("methods", {})
        return {name: info for name, info in methods.items() if name.startswith("/")}

    def _handle_root_command(self, method_name: str, method_args: List[str]):
        """Invoke a root-level publisher command."""
        try:
            method_callable = self.publisher.api.get(method_name, use_smartasync=True)
            positional, keyword = self._split_cli_args(method_args)
            result = method_callable(self.publisher, *positional, **keyword)
            output = self.formatter.format_json(result)
            print(output)
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"Error: {exc}")
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
            payload = {"error": "missing shell identifier", "suggestions": []}
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

    def _generate_completion_payload(
        self, shell: str, cursor: int | None, tokens: List[str]
    ) -> dict:
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

        if handler_name == "_system":
            if depth == 1:
                return self._suggest_system_methods(fragment)
            if depth >= 2:
                return self._suggest_parameters("_system", completed_tokens[1], fragment)
            return []

        if handler_name.startswith("/"):
            return self._suggest_root_parameters(handler_name, fragment)

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

        handlers = self.publisher.get_handlers(channel=self.CHANNEL_CODE)
        root_methods = self._get_root_methods()

        for name, instance in sorted(handlers.items()):
            if fragment and not name.lower().startswith(fragment_lower):
                continue

            description = getattr(instance.__class__, "__doc__", "") or ""
            suggestions.append(
                {
                    "type": "handler",
                    "value": name,
                    "display": name,
                    "description": description.strip(),
                    "inline_hint": "",
                }
            )

        for method_name, info in sorted(root_methods.items()):
            if fragment and not method_name.lower().startswith(fragment_lower):
                continue

            suggestions.append(
                {
                    "type": "root",
                    "value": method_name,
                    "display": method_name,
                    "description": info.get("description", ""),
                    "inline_hint": "",
                }
            )

        return suggestions

    def _suggest_methods(self, handler_name: str, fragment: str) -> List[dict]:
        """Suggest methods for a handler."""
        handler = self.publisher.get_handler(handler_name, channel=self.CHANNEL_CODE)
        if not handler or not hasattr(handler, "api"):
            return []

        schema = handler.api.describe(channel=self.CHANNEL_CODE)
        methods = schema.get("methods", {})
        fragment_lower = fragment.lower()
        suggestions = []

        for method_name, info in methods.items():
            if fragment and not method_name.lower().startswith(fragment_lower):
                continue

            raw_params = info.get("parameters", {})
            param_defs = []
            if isinstance(raw_params, dict):
                for pname, pdata in raw_params.items():
                    pdata = pdata or {}
                    pdata.setdefault("name", pname)
                    param_defs.append(pdata)
            elif isinstance(raw_params, list):
                param_defs = raw_params
            else:
                param_defs = []

            inline_hint = " ".join(
                f"<{param['name']}>" if param.get("required") else f"[{param['name']}]"
                for param in param_defs
            )

            suggestions.append(
                {
                    "type": "method",
                    "value": method_name,
                    "display": method_name,
                    "description": info.get("description", ""),
                    "inline_hint": inline_hint,
                }
            )

        return suggestions

    def _suggest_system_methods(self, fragment: str) -> List[dict]:
        """Suggest methods under the _system handler."""
        if "_system" not in self.publisher.list_handlers(channel=self.CHANNEL_CODE):
            return []

        system_handler = self.publisher.get_handler("_system", channel=self.CHANNEL_CODE)
        schema = system_handler.api.describe(channel=self.CHANNEL_CODE)
        methods = schema.get("methods", {})
        fragment_lower = fragment.lower()
        suggestions = []

        for method_name, info in methods.items():
            if fragment and not method_name.lower().startswith(fragment_lower):
                continue

            suggestions.append(
                {
                    "type": "system",
                    "value": method_name,
                    "display": method_name,
                    "description": info.get("description", ""),
                    "inline_hint": "",
                }
            )

        return suggestions

    def _suggest_parameters(self, handler_name: str, method_name: str, fragment: str) -> List[dict]:
        """Suggest parameters for a specific method."""
        handler = self.publisher.get_handler(handler_name, channel=self.CHANNEL_CODE)
        if not handler or not hasattr(handler, "api"):
            return []

        schema = handler.api.describe(channel=self.CHANNEL_CODE)
        methods = schema.get("methods", {})
        method_schema = methods.get(method_name)

        if not method_schema:
            return []

        raw_params = method_schema.get("parameters", {})
        if isinstance(raw_params, dict):
            params = []
            for pname, pdata in raw_params.items():
                pdata = pdata or {}
                pdata.setdefault("name", pname)
                params.append(pdata)
        elif isinstance(raw_params, list):
            params = raw_params
        else:
            params = []
        fragment_lower = fragment.lower()
        suggestions = []

        for param in params:
            name = param.get("name", "")
            if fragment and not name.lower().startswith(fragment_lower):
                continue

            param_type = param.get("type", "any")
            hint = f"<{param_type}>"
            description = (
                param.get("description")
                or f"{'required' if param.get('required') else 'optional'} parameter"
            )

            suggestions.append(
                {
                    "type": "parameter",
                    "value": name,
                    "display": name,
                    "description": description,
                    "inline_hint": hint,
                    "required": param.get("required", False),
                }
            )

        return suggestions

    def _suggest_root_parameters(self, method_name: str, fragment: str) -> List[dict]:
        """Suggest parameters for root-level commands."""
        root_methods = self._get_root_methods()
        method_schema = root_methods.get(method_name)
        if not method_schema:
            return []

        params = method_schema.get("parameters", [])
        fragment_lower = fragment.lower()
        suggestions = []

        for param in params:
            name = param.get("name", "")
            if fragment and not name.lower().startswith(fragment_lower):
                continue

            param_type = param.get("type", "any")
            suggestions.append(
                {
                    "type": "parameter",
                    "value": name,
                    "display": name,
                    "description": param.get("description") or "",
                    "inline_hint": f"<{param_type}>",
                    "required": param.get("required", False),
                }
            )

        return suggestions

    def _handle_business_command(self, handler_name: str, method_name: str, method_args: list):
        """
        Handle business logic commands.

        Args:
            handler_name: Name of the handler to invoke
            method_name: Method to execute (None = show help)
            method_args: Arguments for the method
        """
        handlers = self.publisher.get_handlers(channel=self.CHANNEL_CODE)
        if handler_name not in handlers:
            print(f"Error: Handler '{handler_name}' not found")
            print(
                f"Available: {', '.join(self.publisher.list_handlers(channel=self.CHANNEL_CODE))}"
            )
            return

        instance = handlers[handler_name]

        # Check has API
        if not hasattr(instance, "api"):
            print(f"Error: Handler '{handler_name}' has no API")
            return

        # No method: show handler help
        if not method_name:
            schema = instance.api.describe(channel=self.CHANNEL_CODE)
            output = self.formatter.format_help(schema)
            print(output)
            return

        # Execute method - SmartSwitch handles EVERYTHING
        try:
            method_callable = instance.api.get(method_name, use_smartasync=True)
            positional, keyword = self._split_cli_args(method_args)
            # method_callable is already bound to the instance
            result = method_callable(*positional, **keyword)
            output = self.formatter.format_json(result)
            print(output)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def _split_cli_args(self, tokens: List[str]) -> Tuple[List[str], dict]:
        """Split CLI tokens into positional and keyword arguments."""
        positional: List[str] = []
        keyword: dict[str, str] = {}
        iterator = iter(tokens)

        for token in iterator:
            if token == "--":
                positional.extend(iterator)
                break

            if token.startswith("--"):
                option = token[2:]
                if not option:
                    raise ValueError("Option name cannot be empty")
                if "=" in option:
                    key, value = option.split("=", 1)
                else:
                    try:
                        value = next(iterator)
                    except StopIteration:
                        raise ValueError(f"Missing value for option '--{option}'")
                    key = option
                keyword[key] = value
                continue

            positional.append(token)

        return positional, keyword
