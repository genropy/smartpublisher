<div align="center">

<img src="assets/logo.png" alt="smpub Logo" width="200"/>

# smpub - Smart Publisher

**CLI/API framework based on SmartSwitch**

</div>

[![PyPI](https://img.shields.io/pypi/v/smpub)](https://pypi.org/project/smpub/)
[![Python](https://img.shields.io/pypi/pyversions/smpub)](https://pypi.org/project/smpub/)
[![License](https://img.shields.io/pypi/l/smpub)](https://github.com/genropy/smpub/blob/main/LICENSE)
[![codecov](https://codecov.io/gh/genropy/smpub/branch/main/graph/badge.svg)](https://codecov.io/gh/genropy/smpub)
[![Documentation](https://readthedocs.org/projects/smpub/badge/?version=latest)](https://smpub.readthedocs.io)
[![Part of Genro-Libs](https://img.shields.io/badge/Genro--Libs-toolkit-blue)](https://github.com/softwell/genro-libs)

Build CLI and API applications with automatic command dispatch using [SmartSwitch](https://github.com/genropy/smartswitch).

## Features

- 🎯 **Publisher Pattern** - Register handlers and expose them via CLI/API
- 🔀 **SmartSwitch Integration** - Rule-based function dispatch
- 💻 **CLI Generation** - Automatic command-line interface
- ✅ **Pydantic Validation** - Automatic type validation and conversion
- 🎨 **Interactive Mode** - Optional questionary-based parameter prompting
- 🌐 **HTTP/API Mode** - FastAPI integration with Swagger UI
- 📝 **Registry System** - Local/global app registration
- 🏗️ **Clean API** - Simple decorator-based handler definition

## Quick Start

### Installation

```bash
pip install smpub

# With HTTP support
pip install smpub[http]

# Interactive mode uses questionary (install separately)
pip install questionary
```

### Basic Example

```python
from smpub import Publisher, PublishedClass
from smartswitch import Switcher

class UserHandler(PublishedClass):
    __slots__ = ('users',)
    api = Switcher(prefix='user_')

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
appendix/smartswitch
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

- [smartswitch](https://github.com/genropy/smartswitch) - Rule-based function dispatch (used by smpub)
- [gtext](https://github.com/genropy/gtext) - Text transformation tool

## License

MIT License - see [LICENSE](https://github.com/genropy/smpub/blob/main/LICENSE) file for details.

## Author

**Genropy Team** - [info@genropy.org](mailto:info@genropy.org)

## Links

- [GitHub Repository](https://github.com/genropy/smpub)
- [Documentation](https://smpub.readthedocs.io)
- [PyPI Package](https://pypi.org/project/smpub/)
- [Issue Tracker](https://github.com/genropy/smpub/issues)
