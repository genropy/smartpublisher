<div align="center">

<img src="assets/logo.png" alt="smpub Logo" width="200"/>

# smpub - Smart Publisher

**CLI/API framework based on SmartRoute**

</div>

[![PyPI](https://img.shields.io/pypi/v/smpub)](https://pypi.org/project/smartpublisher/)
[![Python](https://img.shields.io/pypi/pyversions/smpub)](https://pypi.org/project/smartpublisher/)
[![License](https://img.shields.io/pypi/l/smpub)](https://github.com/genropy/smartpublisher/blob/main/LICENSE)
[![codecov](https://codecov.io/gh/genropy/smartpublisher/branch/main/graph/badge.svg)](https://codecov.io/gh/genropy/smartpublisher)
[![Documentation](https://readthedocs.org/projects/smpub/badge/?version=latest)](https://smartpublisher.readthedocs.io)
[![Part of Genro-Libs](https://img.shields.io/badge/Genro--Libs-toolkit-blue)](https://github.com/softwell/genro-libs)

Build CLI and API applications with automatic command dispatch using [SmartRoute](https://github.com/genropy/smartroute).

## What is smpub?

### The Problem

When you write a Python library, you typically need to provide multiple interfaces:

- **Pythonic API** - Import and use directly in code
- **CLI interface** - Command-line usage for scripts and users
- **HTTP/API** - Web access, integrations, remote calls

Traditionally, this means writing three different interfaces with lots of boilerplate code.

### The Solution

**smpub** (Smart Publisher) offers an elegant approach:

1. **Write your library once** using [SmartRoute](https://github.com/genropy/smartroute) for method dispatch
2. **Get three interfaces automatically**: Python, CLI, and HTTP/API

**[SmartRoute](https://github.com/genropy/smartroute)** provides an elegant Pythonic dispatch system using decorators. **smpub** takes that dispatch system and automatically transforms it into CLI commands and HTTP endpoints.

### Key Concept

```text
Pythonic dispatch (SmartRoute) → Automatic CLI + HTTP (smpub)
```

**One codebase, three interfaces:**

```python
# 1. Your library (uses SmartRoute for elegant dispatch)
from smartroute import Router, route

class MyService:
    api = Router(name='my')

    @api
    def my_operation(self, param: str):
        """Process a parameter."""
        return {"result": param}

# 2. Publishing layer (uses smpub) - just ~20 lines!
from smartpublisher import Publisher

class MyApp(Publisher):
    def on_init(self):
        self.publish("service", MyService())
```

**Result**: Your service is now accessible three ways:

**Python API** (direct import):

```python
from myapp import MyService
service = MyService()
result = service.my_operation("test")
```

**CLI** (automatic):

```bash
python myapp.py service operation test
```

**HTTP API** (automatic):

```bash
# Start server
python myapp.py

# Call API
curl http://localhost:8000/service/operation \
  -H "Content-Type: application/json" \
  -d '{"param": "test"}'

# OpenAPI/Swagger UI at http://localhost:8000/docs
```

### Why SmartRoute?

SmartRoute provides an **elegant Pythonic dispatch** system with:

- Clean decorator syntax (`@api`)
- Plugin chain for cross-cutting concerns (logging, validation, transactions)
- Type-safe method routing
- Composable behavior

When you use SmartRoute, your code is already well-structured for dispatch. smpub simply transforms that dispatch into multiple interfaces.

**Real-world example**: See the [Demo Shop](https://github.com/genropy/smartpublisher-examples) - a complete e-commerce application showing SmartRoute plugins for database transactions, validation, and format negotiation. Published in ~20 lines with smpub.

## Features

- 🎯 **Publisher Pattern** - Register handlers and expose them via CLI/API
- 🔀 **SmartRoute Integration** - Instance-scoped routing and dispatch
- 💻 **CLI Generation** - Automatic command-line interface
- ✅ **Pydantic Validation** - Automatic type validation and conversion
- 🎨 **Interactive Mode** - Optional questionary-based parameter prompting
- 🌐 **HTTP/API Mode** - FastAPI integration with Swagger UI
- 📝 **Registry System** - Local/global app registration
- 🏗️ **Clean API** - Simple decorator-based handler definition

## Quick Start

### Installation

```bash
pip install smartpublisher

# With HTTP support
pip install smartpublisher[http]

# Interactive mode uses questionary (install separately)
pip install questionary
```

### Basic Example

```python
from smartpublisher import Publisher, PublishedClass
from smartroute import Router, route

class UserHandler(PublishedClass):
    __slots__ = ('users',)
    api = Router(name='user')

    def __init__(self):
        self.users = {}

    @api
    def user_add(self, name: str, email: str) -> str:
        """Add a new user."""
        self.users[name] = email
        return f"User {name} added"

    @api
    def user_list(self) -> list:
        """List all users."""
        return list(self.users.keys())

class MainClass(Publisher):
    def initialize(self):
        self.users = UserHandler()
        self.publish('users', self.users, cli=True, openapi=True)

if __name__ == "__main__":
    app = MainClass()
    app.run()  # Auto-detect CLI or HTTP mode
```

### CLI Mode

```bash
# Run commands
python myapp.py users add john john@example.com
python myapp.py users list

# Interactive mode
python myapp.py users add --interactive
```

### HTTP Mode

```bash
# Start HTTP server
python myapp.py

# Access Swagger UI
open http://localhost:8000/docs
```

## Documentation

```{toctree}
:maxdepth: 2
:caption: User Guide

user-guide/installation
user-guide/quickstart
user-guide/publishing-guide
```

```{toctree}
:maxdepth: 2
:caption: Guides

guide/publisher
guide/handlers
guide/cli-mode
guide/http-mode
guide/validation
guide/interactive
guide/best-practices
```

```{toctree}
:maxdepth: 2
:caption: Examples

examples/index
examples/calculator
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/publisher
api/published
api/http
api/interactive
api/validation
```

```{toctree}
:maxdepth: 2
:caption: Appendix

appendix/architecture
appendix/smartroute
philosophy/why-smpub
```

```{toctree}
:maxdepth: 1
:caption: Publishing

publishing-guide
```

## Part of Genro-Libs Family

smpub is part of the [Genro-Libs toolkit](https://github.com/softwell/genro-libs), a collection of general-purpose Python developer tools.

**Related Projects:**

- [smartroute](https://github.com/genropy/smartroute) - Instance-scoped routing engine (used by smpub)
- [gtext](https://github.com/genropy/gtext) - Text transformation tool

## License

MIT License - see [LICENSE](https://github.com/genropy/smartpublisher/blob/main/LICENSE) file for details.

## Author

**Genropy Team** - [info@genropy.org](mailto:info@genropy.org)

## Links

- [GitHub Repository](https://github.com/genropy/smartpublisher)
- [Documentation](https://smartpublisher.readthedocs.io)
- [PyPI Package](https://pypi.org/project/smartpublisher/)
- [Issue Tracker](https://github.com/genropy/smartpublisher/issues)
