<div align="center">

<img src="docs/assets/logo.png" alt="Smart Publisher Logo" width="200"/>

# smpub - Smart Publisher

**CLI/API framework based on SmartRoute**

</div>

[![PyPI version](https://img.shields.io/pypi/v/smartpublisher.svg)](https://pypi.org/project/smartpublisher/)
[![Tests](https://github.com/genropy/smartpublisher/actions/workflows/test.yml/badge.svg)](https://github.com/genropy/smartpublisher/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/genropy/smartpublisher/branch/main/graph/badge.svg)](https://codecov.io/gh/genropy/smartpublisher)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://readthedocs.org/projects/smartpublisher/badge/?version=latest)](https://smartpublisher.readthedocs.io/)
[![Part of Genro-Libs](https://img.shields.io/badge/Part%20of-Genro--Libs-blue)](https://github.com/softwell/genro-libs)
[![LLM Docs](https://img.shields.io/badge/LLM-Docs-purple)](llm-docs/)

---

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

```
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

```python
# Python API (direct import)
from myapp import MyService
service = MyService()
service.my_operation("test")
```

```bash
# CLI (automatic)
python myapp.py service operation test

# HTTP API (automatic)
curl http://localhost:8000/service/operation -d '{"param": "test"}'
# Plus OpenAPI/Swagger at /docs
```

### Why SmartRoute?

SmartRoute provides an **elegant Pythonic dispatch** system with:

- Clean decorator syntax (`@api`)
- Plugin chain for cross-cutting concerns (logging, validation, transactions)
- Type-safe method routing
- Composable behavior

When you use SmartRoute, your code is already well-structured for dispatch. smpub simply transforms that dispatch into multiple interfaces.

**Learn more**: See complete examples at [smartpublisher-examples](https://github.com/genropy/smartpublisher-examples) including Demo Shop (e-commerce system with database operations, custom plugins, and full documentation).

## Features

- 🎯 **Publisher Pattern** - Register handlers and expose them via CLI/API
- 🔀 **SmartRoute Integration** - Instance-scoped routing and dispatch
- 💻 **CLI Generation** - Automatic command-line interface
- ✅ **Pydantic Validation** - Automatic type validation and conversion
- 🎨 **Interactive Mode** - Optional Textual TUI for parameter prompting
- 🌐 **HTTP/API Mode** - FastAPI with OpenAPI/Swagger UI
- 📝 **Registry System** - Local/global app registration

## Installation

```bash
pip install smartpublisher

# With HTTP support
pip install smartpublisher[http]
```

## Quick Start

### Workflow

```
1. Write your code with SmartRoute → 2. Create Publisher → 3. Get CLI + HTTP API
```

### 1. Write Your Service (with SmartRoute)

```python
from typing import Literal
from smartroute import Router, route, RoutedClass

class AccountHandler:
    # If using __slots__, include 'smpublisher'
    __slots__ = ('accounts', 'smpublisher')
    api = Router(name='account')

    def __init__(self):
        self.accounts = {}

    @api
    def account_add(self, name: str, smtp_host: str, smtp_port: int = 587,
                    username: str = "", use_tls: bool = True,
                    auth_method: Literal["plain", "login", "oauth2"] = "plain"):
        """Add a new mail account."""
        self.accounts[name] = {"smtp_host": smtp_host, "smtp_port": smtp_port,
                              "username": username, "use_tls": use_tls}
        return {"success": True, "account": self.accounts[name]}

    @api
    def account_list(self):
        """List all accounts."""
        return {"count": len(self.accounts), "accounts": list(self.accounts.values())}

class MailHandler:
    # If using __slots__, include 'smpublisher'
    __slots__ = ('account_handler', 'messages', 'smpublisher')
    api = Router(name='mail')

    def __init__(self, account_handler):
        self.account_handler = account_handler
        self.messages = []

    @api
    def mail_send(self, account: str, to: str, subject: str, body: str,
                  priority: Literal["low", "normal", "high"] = "normal",
                  html: bool = False):
        """Send an email message."""
        message = {"account": account, "to": to, "subject": subject, "body": body}
        self.messages.append(message)
        return {"success": True, "message_id": len(self.messages)}
```

### 2. Create Publisher (with smpub)

```python
from smartpublisher import Publisher

class MailApp(Publisher):
    def on_init(self):
        self.account = AccountHandler()
        self.mail = MailHandler(self.account)
        # Publish handlers - that's it!
        self.publish('account', self.account)
        self.publish('mail', self.mail)

if __name__ == "__main__":
    app = MailApp()
    app.run()  # Auto-detect CLI or HTTP mode
```

### 3. Use It - Direct Execution

**CLI Mode** (direct execution):

```bash
# Add mail account
python mailapp.py account add work smtp.gmail.com 587 user@work.com

# Send email
python mailapp.py mail send work recipient@example.com "Hello" "Message body"

# Interactive mode (prompts for parameters)
python mailapp.py mail send --interactive
```

**HTTP Mode** (automatic):

```bash
# Start server (no CLI args = HTTP mode)
python mailapp.py
# Opens Swagger UI at http://localhost:8000/docs

# Call API
curl -X POST http://localhost:8000/mail/send \
  -H "Content-Type: application/json" \
  -d '{"account": "work", "to": "user@example.com", "subject": "Hello", "body": "Message"}'
```

### 4. Optional: Register for Global Access

Register your app to use it from anywhere:

```bash
# Register app
smpub register mailapp ~/projects/mailapp

# Now use from anywhere
smpub run mailapp account list
smpub serve mailapp  # Start HTTP server

# List registered apps
smpub list

# Unregister
smpub unregister mailapp
```

**When to use registry?**
- You have multiple apps and want to switch between them
- You want to use your app from any directory
- You're building reusable tools for your team

## Documentation

### Main Documentation

For complete framework documentation, visit [smartpublisher.readthedocs.io](https://smartpublisher.readthedocs.io).

Topics covered:
- Publisher and handler patterns
- Registry system (register/run apps)
- CLI command structure
- HTTP/API mode with FastAPI
- Type validation with Pydantic
- Interactive mode with Textual TUI

### Real-World Example

For a complete example showing SmartRoute plugins, database adapters, and advanced patterns, see:

**[Demo Shop Documentation](https://github.com/genropy/smartpublisher-examples)** - E-commerce library with:
- SQL database system with adapters (SQLite/PostgreSQL)
- Table managers with CRUD operations
- SmartRoute plugin chain (Logging, Pydantic, DbOp)
- Transaction management
- Format negotiation (JSON, Markdown, HTML)
- Published in ~20 lines with smpub

The demo shows how a well-structured SmartRoute application becomes trivial to publish.

## Part of Genro-Libs Family

smpub is part of the [Genro-Libs toolkit](https://github.com/softwell/genro-libs), a collection of general-purpose Python developer tools.

**Related Projects:**

- [smartroute](https://github.com/genropy/smartroute) - Instance-scoped routing engine (used by smpub)
- [gtext](https://github.com/genropy/gtext) - Text transformation tool

## Requirements

- Python 3.10+
- smartroute >= 0.11.0
- pydantic >= 2.0
- textual >= 0.41.0 (optional, for interactive mode)

## Development

```bash
git clone https://github.com/genropy/smartpublisher.git
cd smartpublisher
pip install -e ".[dev]"
pytest
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [Documentation](https://smartpublisher.readthedocs.io)
- [GitHub](https://github.com/genropy/smartpublisher)
- [PyPI](https://pypi.org/project/smartpublisher/)
- [Issue Tracker](https://github.com/genropy/smartpublisher/issues)
