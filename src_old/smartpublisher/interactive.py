"""
Interactive parameter prompting using Textual.
"""

import sys
from typing import Any

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical, Horizontal
    from textual.widgets import Input, Switch, Button, Label, Footer, RadioSet, RadioButton
    from textual.binding import Binding
except ImportError:
    App = None

from .validation import get_parameter_info


def is_textual_available() -> bool:
    """
    Check if textual is installed.

    Returns:
        True if textual is available
    """
    return App is not None


class ParameterForm(App):
    """Textual app for interactive parameter input with Tab/Shift+Tab navigation."""

    CSS = """
    Screen {
        background: $background;
    }

    #form-container {
        width: 100%;
        height: auto;
        padding: 1 2;
    }

    .title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .help {
        color: $text-muted;
        margin-bottom: 2;
    }

    .field-row {
        height: auto;
        width: 100%;
        align: left middle;
    }

    .field-label {
        width: 25;
        content-align: right middle;
        padding: 0 1;
        color: $text;
    }

    .field-label-required {
        width: 25;
        content-align: right middle;
        padding: 0 1;
        color: $warning;
    }

    Input {
        width: 50;
        height: 3;
        border: none;
        padding: 0 1;
    }

    Switch {
        width: auto;
        height: 3;
        padding: 0 1;
    }

    .radio-field {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .radio-label {
        width: auto;
        padding: 0 1;
        margin-bottom: 0;
    }

    .radio-inline {
        layout: horizontal;
        width: 100%;
        height: auto;
        padding: 0 2;
    }

    RadioButton {
        margin-right: 2;
    }

    #buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, params: list[dict[str, Any]]):
        super().__init__()
        self.params = params
        self.values: dict[str, Any] = {}
        self.cancelled = False

    def compose(self) -> ComposeResult:
        """Compose the form UI with all parameter fields in compact layout."""
        with Vertical(id="form-container"):
            yield Label("Interactive Parameter Form", classes="title")
            yield Label("Use Tab/Shift+Tab to navigate, Enter to submit", classes="help")

            # Create widgets for each parameter (compact horizontal layout)
            for param_info in self.params:
                name = param_info["name"]
                param_type = param_info["type"]
                default = param_info["default"]
                required = param_info["required"]

                # Widget on the right based on type
                if param_type == "bool":
                    # Build label for Switch
                    label_text = f"{name} (bool)"
                    if required:
                        label_text += " *"

                    # Horizontal row with label + widget
                    with Horizontal(classes="field-row"):
                        label_class = "field-label-required" if required else "field-label"
                        yield Label(label_text, classes=label_class)
                        value = bool(default if default is not None else True)
                        yield Switch(value=value, id=f"field_{name}")

                elif param_type.startswith("Literal["):
                    # For Literal types, use RadioSet with buttons on same line
                    literal_str = param_type[8:-1]  # Remove "Literal[" and "]"
                    choices = [choice.strip().strip("'\"") for choice in literal_str.split(",")]
                    initial = str(default) if default is not None else choices[0]

                    # Build label
                    label_text = f"{name}"
                    if required:
                        label_text += " *"

                    # Vertical container for label + radio buttons
                    with Vertical(classes="radio-field"):
                        label_class = "field-label-required" if required else "field-label"
                        yield Label(label_text, classes=label_class + " radio-label")

                        # Horizontal RadioSet with all buttons inline
                        with RadioSet(id=f"field_{name}", classes="radio-inline"):
                            for choice in choices:
                                yield RadioButton(choice, value=(choice == initial))
                else:
                    # Build label for regular input
                    label_text = f"{name} ({param_type})"
                    if required:
                        label_text += " *"

                    # Horizontal row with label + input
                    with Horizontal(classes="field-row"):
                        label_class = "field-label-required" if required else "field-label"
                        yield Label(label_text, classes=label_class)
                        default_str = str(default) if default is not None else ""
                        placeholder = "Required" if required else "Optional"
                        yield Input(value=default_str, placeholder=placeholder, id=f"field_{name}")

            # Buttons
            with Horizontal(id="buttons"):
                yield Button("Submit", variant="primary", id="submit")
                yield Button("Cancel", variant="default", id="cancel")

        yield Footer()

    def action_cancel(self) -> None:
        """Handle cancel action."""
        self.cancelled = True
        self.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "submit":
            # Collect values from all fields
            for param_info in self.params:
                name = param_info["name"]
                widget = self.query_one(f"#field_{name}")

                if isinstance(widget, Switch):
                    self.values[name] = widget.value
                elif isinstance(widget, RadioSet):
                    # Get the selected radio button label
                    pressed = widget.pressed_button
                    if pressed:
                        self.values[name] = pressed.label.plain
                    else:
                        self.values[name] = ""
                elif isinstance(widget, Input):
                    self.values[name] = widget.value

            self.exit()
        elif event.button.id == "cancel":
            self.action_cancel()


def prompt_for_parameters(method) -> list[str]:
    """
    Interactively prompt for all method parameters using Textual.

    Users can navigate between fields using Tab (forward) and Shift+Tab (backward).

    Args:
        method: The method to prompt for

    Returns:
        List of string values (in correct order)

    Example:
        >>> def test_method(name: str, age: int = 25, enabled: bool = True):
        ...     pass
        >>> args = prompt_for_parameters(test_method)
        >>> # User sees a form with all parameters, can navigate back/forward
        >>> args
        ['Alice', '30', 'True']
    """
    # Check if textual is available
    if not is_textual_available():
        print("Error: textual is not installed")
        print("\nTo use interactive mode, install textual:")
        print("  pip install textual")
        sys.exit(1)

    # Get parameter info
    params = get_parameter_info(method)

    if not params:
        return []

    # Create and run the form app
    app = ParameterForm(params)
    app.run()

    # Check if cancelled
    if app.cancelled:
        print("\nCancelled.")
        sys.exit(0)

    # Convert collected values to list in correct parameter order
    values = []
    for param_info in params:
        name = param_info["name"]
        value = app.values.get(name, "")

        # Convert boolean to string "True"/"False"
        if param_info["type"] == "bool":
            value = str(value)
        # Ensure all values are strings
        elif not isinstance(value, str):
            value = str(value)

        # Handle empty optional fields
        if not value and not param_info["required"] and param_info["default"] is not None:
            value = str(param_info["default"])

        values.append(value)

    return values
