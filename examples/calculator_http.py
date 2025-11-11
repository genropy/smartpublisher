#!/usr/bin/env python
"""
Calculator example with HTTP/Swagger UI support.

Run with:
    python examples/calculator_http.py           # HTTP mode on port 8000
    python examples/calculator_http.py 8080      # HTTP mode on port 8080
    python examples/calculator_http.py calc add 10 20  # CLI mode

Then visit: http://localhost:8000/docs for Swagger UI
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smpub import Publisher, PublishedClass
from smartswitch import Switcher


class CalculatorHandler(PublishedClass):
    """
    Calculator handler with basic arithmetic operations.

    Demonstrates Pydantic validation and HTTP API exposure.
    """

    __slots__ = ("history",)
    api = Switcher(prefix="calc_")

    def __init__(self):
        """Initialize calculator with empty history."""
        self.history = []

    @api
    def calc_add(self, a: int, b: int) -> int:
        """
        Add two integers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result

    @api
    def calc_subtract(self, a: int, b: int) -> int:
        """
        Subtract two integers.

        Args:
            a: First number
            b: Number to subtract

        Returns:
            Difference (a - b)
        """
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result

    @api
    def calc_multiply(self, x: float, y: float, precision: int = 2) -> float:
        """
        Multiply two numbers with optional precision.

        Args:
            x: First number
            y: Second number
            precision: Decimal places (default: 2)

        Returns:
            Product rounded to precision
        """
        result = round(x * y, precision)
        self.history.append(f"multiply({x}, {y}) = {result}")
        return result

    @api
    def calc_divide(self, numerator: float, denominator: float) -> float:
        """
        Divide two numbers.

        Args:
            numerator: Number to divide
            denominator: Number to divide by

        Returns:
            Result of division

        Raises:
            ValueError: If denominator is zero
        """
        if denominator == 0:
            raise ValueError("Cannot divide by zero")

        result = numerator / denominator
        self.history.append(f"divide({numerator}, {denominator}) = {result}")
        return result

    @api
    def calc_power(self, base: float, exponent: int) -> float:
        """
        Raise base to exponent.

        Args:
            base: Base number
            exponent: Exponent

        Returns:
            Result of base^exponent
        """
        result = base**exponent
        self.history.append(f"power({base}, {exponent}) = {result}")
        return result

    @api
    def calc_history(self) -> list:
        """
        Get calculation history.

        Returns:
            List of previous calculations
        """
        return self.history

    @api
    def calc_clear(self) -> str:
        """
        Clear calculation history.

        Returns:
            Confirmation message
        """
        count = len(self.history)
        self.history.clear()
        return f"Cleared {count} entries from history"


class CalculatorApp(Publisher):
    """
    Calculator application with CLI and HTTP/API support.

    Features:
    - Basic arithmetic operations
    - Calculation history
    - Pydantic validation
    - Interactive CLI mode
    - FastAPI + Swagger UI
    """

    def initialize(self):
        """Initialize and register handlers."""
        self.calculator = CalculatorHandler()

        # Publish with both CLI and OpenAPI support
        self.publish(
            "calc",
            self.calculator,
            cli=True,  # Enable CLI access
            openapi=True,  # Enable HTTP/API access
            cli_name="calc",
            http_path="/calc",
        )


def main():
    """Entry point for the application."""
    app = CalculatorApp()

    # Parse custom port if provided as first argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            # Run HTTP mode with custom port
            app.run(mode="http", port=port)
        except ValueError:
            # Not a port number, run CLI mode
            app.run(mode="cli")
    else:
        # No args: run HTTP mode on default port
        app.run(mode="http", port=8000)


if __name__ == "__main__":
    main()
