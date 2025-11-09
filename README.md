# smpub - Smart Publisher

**CLI/API framework based on SmartSwitch**

[![PyPI](https://img.shields.io/pypi/v/smpub)](https://pypi.org/project/smpub/)
[![Python](https://img.shields.io/pypi/pyversions/smpub)](https://pypi.org/project/smpub/)
[![License](https://img.shields.io/pypi/l/smpub)](https://github.com/genropy/smpub/blob/main/LICENSE)
[![Part of Genro-Libs](https://img.shields.io/badge/Genro--Libs-toolkit-blue)](https://github.com/softwell/genro-libs)

Build CLI and API applications with automatic command dispatch using [SmartSwitch](https://github.com/genropy/smartswitch).

## Features

- 🎯 **Publisher Pattern** - Register handlers and expose them via CLI/API
- 🔀 **SmartSwitch Integration** - Rule-based function dispatch
- 💻 **CLI Generation** - Automatic command-line interface
- 🌐 **API Exposure** - OpenAPI/HTTP endpoints (planned)
- 📝 **Registry System** - Local/global app registration
- 🎨 **Clean API** - Simple decorator-based handler definition

## Installation

```bash
pip install smpub
```

## Quick Start

### 1. Create a Handler

```python
# myapp/handlers.py
from smpub import PublishedClass
from smartswitch import Switcher

class UserHandler(PublishedClass):
    __slots__ = ('users',)
    api = Switcher(prefix='user_')

    def __init__(self):
        self.users = {}

    @api
    def user_add(self, name, email):
        """Add a new user."""
        self.users[name] = email
        return f"User {name} added"

    @api
    def user_list(self):
        """List all users."""
        return list(self.users.keys())
```

### 2. Create an App

```python
# myapp/main.py
from smpub import Publisher
from .handlers import UserHandler

class MainClass(Publisher):
    def initialize(self):
        self.users = UserHandler()
        self.publish('users', self.users, cli=True, openapi=True)

if __name__ == "__main__":
    app = MainClass()
    app.run()  # Auto-detect CLI or HTTP mode
```

### 3. Register and Run

```bash
# Register your app
smpub add myapp --path ~/projects/myapp

# List registered apps
smpub list

# Run commands
smpub myapp users add john john@example.com
smpub myapp users list

# Remove app
smpub remove myapp
```

## Registry System

### Local Registry (per directory)

```bash
# Register app locally (creates ./.published)
smpub add myapp --path ~/projects/myapp

# List local apps
smpub list

# Remove from local registry
smpub remove myapp
```

### Global Registry (system-wide)

```bash
# Register globally (creates ~/.smartlibs/publisher/registry.json)
smpub add myapp --path ~/projects/myapp --global

# List global apps
smpub list --global

# Remove from global registry
smpub remove myapp --global
```

## Architecture

```
Publisher (your app)
  ├─ parent_api: Switcher      # Root API registry
  └─ published_instances
      └─ 'users' → UserHandler
          └─ api: Switcher      # Handler API
              ├─ user_add
              ├─ user_list
              └─ ...
```

## Key Classes

### `Publisher`

Base class for applications:

```python
class MyApp(Publisher):
    def initialize(self):
        # Called after parent_api is created
        # Register your handlers here
        self.publish('name', handler_instance)
```

### `PublishedClass`

Mixin for handler classes:

```python
class MyHandler(PublishedClass):
    __slots__ = ('data',)  # Add your slots
    # parent_api slot provided by PublishedClass

    api = Switcher(...)  # Define your API
```

## CLI Command Structure

```bash
smpub <app> <handler> <method> [args...]
```

Example:

```bash
smpub myapp users add john john@example.com
       │     │     │   └─ method args
       │     │     └─ method name
       │     └─ handler name
       └─ app name
```

## API Exposure Control

Control which handlers are exposed where:

```python
# CLI only
self.publish('internal', handler, cli=True, openapi=False)

# API only
self.publish('api', handler, cli=False, openapi=True)

# Both (default)
self.publish('public', handler, cli=True, openapi=True)

# Neither (monitoring/internal)
self.publish('metrics', handler, cli=False, openapi=False)
```

## Part of Genro-Libs Family

smpub is part of the [Genro-Libs toolkit](https://github.com/softwell/genro-libs), a collection of general-purpose Python developer tools.

**Related Projects:**
- [smartswitch](https://github.com/genropy/smartswitch) - Rule-based function dispatch (used by smpub)
- [gtext](https://github.com/genropy/gtext) - Text transformation tool

## Requirements

- Python 3.10+
- smartswitch >= 0.1.0

## Development

```bash
# Clone the repository
git clone https://github.com/genropy/smpub.git
cd smpub

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black src/ tests/
ruff check src/ tests/
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Genropy Team** - [info@genropy.org](mailto:info@genropy.org)

## Links

- [Documentation](https://smpub.readthedocs.io) (coming soon)
- [GitHub](https://github.com/genropy/smpub)
- [PyPI](https://pypi.org/project/smpub/)
- [Issue Tracker](https://github.com/genropy/smpub/issues)
