# Publishing Guide: How to Expose Your Library with smpub

This guide shows you how to take an existing Python library and expose it via CLI and API using smpub.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step-by-Step Guide](#step-by-step-guide)
- [Handler Requirements](#handler-requirements)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Complete Example](#complete-example)

## Overview

**Goal**: Take an existing library and make it accessible via:
- Command-line interface (CLI)
- HTTP API with OpenAPI documentation (planned)
- Interactive parameter prompting

**The smpub Pattern**:
1. Wrap your library in **Handler classes**
2. Create a **Publisher application** that registers handlers
3. Choose exposure modes (CLI, API, or both)

## Prerequisites

Your existing library should have:
- Well-defined functions/methods with clear responsibilities
- Type hints on parameters (for automatic validation)
- Docstrings (for auto-generated help)

**Example library to publish** (`mylib/calculator.py`):

```python
"""Calculator library - business logic."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(x: float, y: float, precision: int = 2) -> float:
    """Multiply two numbers with optional precision."""
    result = x * y
    return round(result, precision)

def divide(numerator: float, denominator: float) -> float:
    """Divide two numbers."""
    if denominator == 0:
        raise ValueError("Cannot divide by zero")
    return numerator / denominator
```

## Step-by-Step Guide

### Step 1: Install smpub

```bash
pip install smpub

# Optional: for interactive mode
brew install dialog  # macOS
```

### Step 2: Create Handler Classes

Create handlers that wrap your library's functionality. Place them in a `handlers/` directory.

**File**: `myapp/handlers/calculator_handler.py`

```python
"""Handler that exposes calculator functions via smpub."""

from smartswitch import Switcher
from smpub import PublishedClass

# Import your existing library
from mylib import calculator


class CalculatorHandler(PublishedClass):
    """
    Handler for calculator operations.

    Wraps the calculator library and exposes it via CLI/API.
    """

    # Define slots (optional, but recommended for memory efficiency)
    __slots__ = ('history',)

    # Create API with prefix to avoid naming conflicts
    api = Switcher(prefix='calc_')

    def __init__(self):
        """Initialize handler with empty history."""
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
        result = calculator.add(a, b)
        self.history.append(f"add({a}, {b}) = {result}")
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
        result = calculator.multiply(x, y, precision)
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
        result = calculator.divide(numerator, denominator)
        self.history.append(f"divide({numerator}, {denominator}) = {result}")
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
        self.history.clear()
        return "History cleared"
```

### Step 3: Create Publisher Application

**File**: `myapp/main.py`

```python
"""Main application that publishes handlers."""

from smpub import Publisher
from myapp.handlers.calculator_handler import CalculatorHandler


class CalculatorApp(Publisher):
    """
    Calculator application.

    Exposes calculator functionality via CLI and API.
    """

    def initialize(self):
        """
        Initialize and register handlers.

        This method is called automatically by Publisher.__init__()
        """
        # Create handler instances
        self.calculator = CalculatorHandler()

        # Publish handlers with exposure control
        self.publish(
            'calc',                    # Handler name (used in CLI)
            self.calculator,           # Handler instance
            cli=True,                  # Enable CLI access
            openapi=True,              # Enable API access (future)
            cli_name='calc',           # Optional: override CLI name
            http_path='/api/calc'      # Optional: API path
        )


def main():
    """Entry point for the application."""
    app = CalculatorApp()
    app.run()  # Auto-detects CLI or HTTP mode


if __name__ == "__main__":
    main()
```

### Step 4: Create Entry Point

**File**: `pyproject.toml` (add to your project)

```toml
[project.scripts]
mycalc = "myapp.main:main"
```

Or create a simple script:

**File**: `mycalc` (make executable with `chmod +x mycalc`)

```python
#!/usr/bin/env python
"""Calculator CLI entry point."""

from myapp.main import main

if __name__ == "__main__":
    main()
```

### Step 5: Test Your CLI

```bash
# Install in development mode
pip install -e .

# Test the CLI
mycalc --help
# Shows: CalculatorApp with 'calc' handler

mycalc calc --help
# Shows: All calculator methods with parameters

mycalc calc add 10 20
# Output: 30

mycalc calc multiply 3.5 2.0
# Output: 7.0

mycalc calc multiply 3.5 2.0 3
# Output: 7.000 (3 decimal places)

# Interactive mode
mycalc calc divide --interactive
# Prompts for numerator and denominator

# Check history
mycalc calc history
# Output: List of calculations
```

## Handler Requirements

### Required Elements

1. **Switcher API definition**:
   ```python
   api = Switcher(prefix='handler_')
   ```

2. **Type-hinted methods**:
   ```python
   @api
   def handler_method(self, param: int, optional: str = "default") -> str:
       """Docstring for help text."""
       pass
   ```

3. **Clear docstrings** (for auto-generated help):
   ```python
   """
   One-line summary.

   Longer description (optional).

   Args:
       param: Description

   Returns:
       Description
   """
   ```

### Optional but Recommended

1. **Use PublishedClass** when using `__slots__`:
   ```python
   from smpub import PublishedClass

   class MyHandler(PublishedClass):
       __slots__ = ('data', 'config')  # Your slots
       # 'publisher' slot provided by PublishedClass
   ```

2. **Prefix convention**: Use prefix that matches handler purpose:
   - `user_` for user operations
   - `file_` for file operations
   - `db_` for database operations

3. **State management**: Store handler state in instance variables:
   ```python
   def __init__(self):
       self.cache = {}
       self.connections = []
   ```

## Best Practices

### 1. Separation of Concerns

**✅ Good**: Thin handlers that delegate to business logic

```python
class DataHandler(PublishedClass):
    api = Switcher(prefix='data_')

    def __init__(self):
        self.processor = DataProcessor()  # Your library

    @api
    def data_process(self, input_file: str, format: str = 'json'):
        """Process data file."""
        # Validate with Pydantic (automatic)
        # Delegate to business logic
        result = self.processor.process(input_file, format)
        return result
```

**❌ Bad**: Business logic mixed in handler

```python
class DataHandler(PublishedClass):
    api = Switcher(prefix='data_')

    @api
    def data_process(self, input_file: str, format: str = 'json'):
        # Avoid putting complex logic here
        with open(input_file) as f:
            data = json.load(f)
        # ... complex processing ...
        return processed_data
```

### 2. Type Hints for Free Validation

**✅ Good**: Use specific types

```python
@api
def calc_power(self, base: float, exponent: int, modulo: int = None) -> float:
    """Calculate power with optional modulo."""
    result = pow(base, exponent, modulo)
    return result
```

**Benefits**:
- Automatic validation: `"10"` → `10` (int)
- Clear error messages on invalid input
- Type information in help text

### 3. Clear Documentation

**✅ Good**: Comprehensive docstrings

```python
@api
def user_create(self, username: str, email: str, role: str = 'user') -> dict:
    """
    Create a new user account.

    Creates a user with the specified credentials and assigns
    the given role. Email must be unique.

    Args:
        username: Unique username (3-20 chars)
        email: Valid email address
        role: User role (default: 'user', options: 'user', 'admin')

    Returns:
        Dictionary with user details and ID

    Raises:
        ValueError: If email already exists

    Example:
        >>> user_create("alice", "alice@example.com", "admin")
        {"id": 1, "username": "alice", "role": "admin"}
    """
    return self.user_service.create(username, email, role)
```

### 4. Error Handling

**✅ Good**: Let exceptions bubble up with clear messages

```python
@api
def file_read(self, path: str) -> str:
    """Read file contents."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path) as f:
            return f.read()
    except PermissionError:
        raise PermissionError(f"Cannot read file: {path} (permission denied)")
```

smpub will catch and display exceptions properly in CLI.

### 5. Handler Organization

**For simple apps**: Single handler file

```
myapp/
├── main.py
└── handler.py
```

**For complex apps**: Multiple handlers by domain

```
myapp/
├── main.py
└── handlers/
    ├── __init__.py
    ├── user_handler.py
    ├── file_handler.py
    └── database_handler.py
```

### 6. Publisher Best Practices

**✅ Good**: Descriptive names and exposure control

```python
def initialize(self):
    # Public handlers (CLI + API)
    self.users = UserHandler()
    self.publish('users', self.users, cli=True, openapi=True)

    # Internal handlers (CLI only)
    self.admin = AdminHandler()
    self.publish('admin', self.admin, cli=True, openapi=False)

    # Monitoring (neither CLI nor API)
    self.metrics = MetricsHandler()
    self.publish('metrics', self.metrics, cli=False, openapi=False)
```

## Common Patterns

### Pattern 1: Database Operations

```python
class DatabaseHandler(PublishedClass):
    __slots__ = ('db', 'connection')
    api = Switcher(prefix='db_')

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None

    @api
    def db_connect(self) -> str:
        """Connect to database."""
        self.connection = create_connection(self.connection_string)
        return "Connected"

    @api
    def db_query(self, sql: str, params: str = None) -> list:
        """Execute SQL query."""
        if not self.connection:
            raise RuntimeError("Not connected. Run 'db connect' first")
        return self.connection.execute(sql, params)
```

### Pattern 2: File Operations

```python
class FileHandler(PublishedClass):
    __slots__ = ('current_dir',)
    api = Switcher(prefix='file_')

    def __init__(self):
        self.current_dir = os.getcwd()

    @api
    def file_list(self, pattern: str = '*') -> list:
        """List files matching pattern."""
        return glob.glob(os.path.join(self.current_dir, pattern))

    @api
    def file_read(self, filename: str, encoding: str = 'utf-8') -> str:
        """Read file contents."""
        path = os.path.join(self.current_dir, filename)
        with open(path, encoding=encoding) as f:
            return f.read()
```

### Pattern 3: Service Integration

```python
class APIHandler(PublishedClass):
    __slots__ = ('client', 'api_key')
    api = Switcher(prefix='api_')

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = APIClient(api_key)

    @api
    def api_get(self, endpoint: str, params: str = None) -> dict:
        """Make GET request to API."""
        return self.client.get(endpoint, params)

    @api
    def api_post(self, endpoint: str, data: str) -> dict:
        """Make POST request to API."""
        return self.client.post(endpoint, json.loads(data))
```

## Complete Example

Here's a complete working example that wraps a hypothetical data processing library:

**File**: `myapp/handlers/data_handler.py`

```python
"""Handler for data processing operations."""

from smartswitch import Switcher
from smpub import PublishedClass
from mylib.processor import DataProcessor
from mylib.validators import SchemaValidator


class DataHandler(PublishedClass):
    """
    Data processing handler.

    Provides CLI/API access to data processing operations.
    """

    __slots__ = ('processor', 'validator', 'cache')
    api = Switcher(prefix='data_')

    def __init__(self, cache_size: int = 100):
        """
        Initialize data handler.

        Args:
            cache_size: Maximum number of cached results
        """
        self.processor = DataProcessor()
        self.validator = SchemaValidator()
        self.cache = {}

    @api
    def data_load(self, filename: str, format: str = 'json') -> dict:
        """
        Load data file.

        Args:
            filename: Path to data file
            format: File format (json, csv, xml)

        Returns:
            Parsed data as dictionary
        """
        if filename in self.cache:
            return self.cache[filename]

        data = self.processor.load(filename, format)
        self.cache[filename] = data
        return data

    @api
    def data_transform(self, input_file: str, output_file: str,
                      operations: str) -> str:
        """
        Transform data file.

        Args:
            input_file: Source file
            output_file: Destination file
            operations: Comma-separated operations (e.g., "sort,dedupe,validate")

        Returns:
            Success message with statistics
        """
        data = self.data_load(input_file)

        ops = [op.strip() for op in operations.split(',')]
        for op in ops:
            data = self.processor.apply_operation(data, op)

        self.processor.save(data, output_file)
        return f"Processed {len(data)} records with {len(ops)} operations"

    @api
    def data_validate(self, filename: str, schema: str) -> dict:
        """
        Validate data against schema.

        Args:
            filename: Data file to validate
            schema: Path to schema file

        Returns:
            Validation results with errors and warnings
        """
        data = self.data_load(filename)
        results = self.validator.validate(data, schema)

        return {
            'valid': results.is_valid,
            'errors': results.errors,
            'warnings': results.warnings
        }

    @api
    def data_stats(self, filename: str) -> dict:
        """
        Get statistics about data file.

        Args:
            filename: Data file to analyze

        Returns:
            Statistics dictionary
        """
        data = self.data_load(filename)

        return {
            'records': len(data),
            'fields': list(data[0].keys()) if data else [],
            'size_mb': self.processor.get_size(filename) / (1024 * 1024)
        }
```

**File**: `myapp/main.py`

```python
"""Main application."""

from smpub import Publisher
from myapp.handlers.data_handler import DataHandler


class DataApp(Publisher):
    """Data processing application."""

    def initialize(self):
        """Register handlers."""
        self.data = DataHandler(cache_size=50)
        self.publish('data', self.data, cli=True, openapi=True)


def main():
    """Entry point."""
    app = DataApp()
    app.run()


if __name__ == "__main__":
    main()
```

**Usage**:

```bash
# Load and process data
dataapp data load input.json
dataapp data transform input.json output.json "sort,dedupe,validate"
dataapp data validate output.json schema.json
dataapp data stats output.json

# Interactive mode
dataapp data transform --interactive
# Prompts for: input_file, output_file, operations
```

## Summary

**Key Takeaways**:

1. **Handlers wrap business logic** - Keep them thin
2. **Use type hints** - Get free validation
3. **Write clear docstrings** - Auto-generated help
4. **Choose exposure carefully** - CLI, API, or both
5. **Let smpub handle** - Validation, errors, help generation

**Next Steps**:

- Read the [Architecture documentation](../appendix/architecture.md)
- Check the test files for implementation examples
- See [examples](../examples/index.md) for working code

---

**Questions?** Open an issue at https://github.com/genropy/smpub/issues
