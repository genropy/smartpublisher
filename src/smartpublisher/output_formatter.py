"""
OutputFormatter - Format structured data at transport boundary.

This is where print statements belong - at the EDGE, not in business logic.

Key principle: Business logic returns structured data (dict/JSON),
OutputFormatter converts it to user-friendly format (text/table/markdown/html).
"""

import json
from typing import Any


class OutputFormatter:
    """
    Format structured data for display.

    This class handles the EDGE of the system - converting structured
    data into user-friendly formats. This is the ONLY place where
    print-like formatting should happen.
    """

    @staticmethod
    def format_json(data: Any, pretty: bool = True) -> str:
        """
        Format data as JSON.

        Args:
            data: Data to format
            pretty: Pretty print with indentation

        Returns:
            str: JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def format_table(data: dict) -> str:
        """
        Format data as simple text table.

        Args:
            data: Dict with 'headers' and 'rows' keys

        Returns:
            str: Formatted table
        """
        if not isinstance(data, dict):
            return str(data)

        if "handlers" in data:
            # Format handler list
            lines = ["Handlers:"]
            for name, info in data["handlers"].items():
                lines.append(f"  {name:20} {info.get('class', 'Unknown')}")
                if info.get("methods"):
                    for method in info["methods"]:
                        lines.append(f"    - {method}")
            return "\n".join(lines)

        # Generic dict formatting
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def format_error(error_data: dict) -> str:
        """
        Format error message.

        Args:
            error_data: Error information

        Returns:
            str: Formatted error
        """
        if isinstance(error_data, dict) and "error" in error_data:
            msg = f"Error: {error_data['error']}"
            if "available" in error_data:
                msg += f"\nAvailable: {', '.join(error_data['available'])}"
            return msg

        return str(error_data)

    @staticmethod
    def format_help(api_schema: dict) -> str:
        """
        Format help from API schema.

        Args:
            api_schema: API schema from Switcher.describe()

        Returns:
            str: Formatted help text
        """
        lines = []

        if "methods" in api_schema:
            lines.append("Available commands:")
            for method_name, method_info in sorted(api_schema["methods"].items()):
                # Build parameter string
                params = []
                for param in method_info.get("parameters", []):
                    if param.get("required"):
                        params.append(f"<{param['name']}:{param.get('type', 'any')}>")
                    else:
                        default = param.get("default", "None")
                        params.append(f"[{param['name']}:{param.get('type', 'any')}={default}]")

                param_str = " ".join(params)
                desc = method_info.get("description", "No description")

                lines.append(f"  {method_name:20} {param_str:30} {desc}")

        return "\n".join(lines)
