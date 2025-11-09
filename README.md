<div align="center">

<img src="docs/assets/logo.png" alt="smpub Logo" width="200"/>

# smpub - Smart Publisher

**CLI/API framework based on SmartSwitch**

</div>

[![PyPI version](https://img.shields.io/pypi/v/smpub.svg)](https://pypi.org/project/smpub/)
[![Tests](https://github.com/genropy/smpub/actions/workflows/test.yml/badge.svg)](https://github.com/genropy/smpub/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/genropy/smpub/branch/main/graph/badge.svg)](https://codecov.io/gh/genropy/smpub)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://readthedocs.org/projects/smpub/badge/?version=latest)](https://smpub.readthedocs.io/)

---

Build CLI and API applications with automatic command dispatch using [SmartSwitch](https://github.com/genropy/smartswitch).

## Features

- 🎯 **Publisher Pattern** - Register handlers and expose them via CLI/API
- 🔀 **SmartSwitch Integration** - Rule-based function dispatch
- 💻 **CLI Generation** - Automatic command-line interface
- ✅ **Pydantic Validation** - Automatic type validation and conversion
- 🎨 **Interactive Mode** - Optional gum-based parameter prompting
- 🌐 **HTTP/API Mode** - FastAPI with OpenAPI/Swagger UI
- 📝 **Registry System** - Local/global app registration

## Installation

```bash
pip install smpub

# With HTTP support
pip install smpub[http]
```

## Quick Start

### 1. Create Handlers

```python
from typing import Literal
from smpub import PublishedClass
from smartswitch import Switcher

class AccountHandler(PublishedClass):
    __slots__ = ('accounts',)
    api = Switcher(prefix='account_')

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

class MailHandler(PublishedClass):
    __slots__ = ('account_handler', 'messages')
    api = Switcher(prefix='mail_')

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

### 2. Create an App

```python
from smpub import Publisher

class MainClass(Publisher):
    def initialize(self):
        self.account = AccountHandler()
        self.mail = MailHandler(self.account)
        self.publish('account', self.account, cli=True, openapi=True)
        self.publish('mail', self.mail, cli=True, openapi=True)

if __name__ == "__main__":
    app = MainClass()
    app.run()  # Auto-detect CLI or HTTP mode
```

### 3. Use It

**CLI Mode:**
```bash
# Register your app
smpub add mailapp --path ~/projects/mailapp

# Add mail account
smpub mailapp account add work smtp.gmail.com 587 user@work.com

# Send email
smpub mailapp mail send work recipient@example.com "Hello" "Message body"
```

**HTTP Mode:**

```bash
# Start server
python mailapp.py
# Opens Swagger UI at http://localhost:8000/docs

# Call API
curl -X POST http://localhost:8000/mail/send \
  -H "Content-Type: application/json" \
  -d '{"to": "user@example.com", "subject": "Hello", "body": "Message"}'
```

**Interactive Mode:**

```bash
smpub mailapp mail send --interactive
# Prompts for each parameter with type hints
```

## Documentation

For complete documentation, visit [smpub.readthedocs.io](https://smpub.readthedocs.io).

Topics covered:

- Publisher and handler patterns
- CLI command structure
- Type validation with Pydantic
- Interactive mode with gum
- HTTP/API mode with FastAPI
- Registry system (local/global)
- Architecture and design

## Part of Genro-Libs Family

smpub is part of the [Genro-Libs toolkit](https://github.com/softwell/genro-libs), a collection of general-purpose Python developer tools.

**Related Projects:**

- [smartswitch](https://github.com/genropy/smartswitch) - Rule-based function dispatch (used by smpub)
- [gtext](https://github.com/genropy/gtext) - Text transformation tool

## Requirements

- Python 3.10+
- smartswitch >= 0.1.0
- pydantic >= 2.0
- [gum](https://github.com/charmbracelet/gum) (optional, for interactive mode)

## Development

```bash
git clone https://github.com/genropy/smpub.git
cd smpub
pip install -e ".[dev]"
pytest
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [Documentation](https://smpub.readthedocs.io)
- [GitHub](https://github.com/genropy/smpub)
- [PyPI](https://pypi.org/project/smpub/)
- [Issue Tracker](https://github.com/genropy/smpub/issues)
