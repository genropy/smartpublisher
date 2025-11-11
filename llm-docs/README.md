# smpub - LLM Quick Reference

## Core Purpose
CLI/API framework based on SmartSwitch for building command-line and web applications with automatic dispatch, validation, and OpenAPI support.

## Installation
```bash
pip install smpub
```

## Essential Patterns

### 1. Basic Publisher Application
```python
from smpub import Publisher
from smartswitch import Switcher

class MyHandler:
    # If using __slots__, include 'smpublisher'
    __slots__ = ('data', 'smpublisher')
    api = Switcher(prefix='cmd_')

    def __init__(self):
        self.data = {}

    @api
    def cmd_add(self, key: str, value: int):
        """Add a key-value pair."""
        self.data[key] = value
        return f"Added {key}={value}"

    @api
    def cmd_get(self, key: str):
        """Get a value by key."""
        return self.data.get(key)

class MyApp(Publisher):
    def initialize(self):
        self.handler = MyHandler()
        # Publish handler for both CLI and HTTP
        self.publish('handler', self.handler)

if __name__ == "__main__":
    app = MyApp()
    app.run()  # Auto-detects CLI or HTTP mode
```

### 2. CLI Mode Usage
```bash
# Get help
python myapp.py

# Handler-specific help
python myapp.py handler --help

# Execute method
python myapp.py handler add mykey 42
python myapp.py handler get mykey

# Interactive mode
python myapp.py handler add --interactive
```

### 3. HTTP/FastAPI Mode
```python
class MyApp(Publisher):
    def initialize(self):
        self.publish('api', self.handler, http_path="/api/v1")

# Run HTTP server
app = MyApp()
app.run(mode="http", port=8000)
```

Access at:
- Swagger UI: `http://localhost:8000/docs`
- POST endpoint: `http://localhost:8000/api/v1/add`

### 4. Exposure Control
```python
# CLI only (no OpenAPI/HTTP)
self.publish('internal', handler, cli=True, openapi=False)

# HTTP only (no CLI)
self.publish('api', handler, cli=False, openapi=True)

# Both (default)
self.publish('public', handler)  # cli=True, openapi=True
```

### 5. Automatic Type Validation
```python
class TypedHandler:
    api = Switcher()

    @api
    def process(self, name: str, age: int, active: bool = True):
        """Process with type validation."""
        return f"{name}, {age}, {active}"

# CLI automatically validates and converts types
# python myapp.py handler process Alice 30 false
# HTTP validates via Pydantic models
```

### 6. Async Methods Support
```python
class AsyncHandler:
    api = Switcher()

    @api
    async def fetch_data(self, user_id: int):
        """Async method - works in both CLI and HTTP."""
        # Async operations here
        return data

# Works in both sync (CLI) and async (HTTP) contexts via smartasync
```

### 7. Multiple Handlers
```python
class MyApp(Publisher):
    def initialize(self):
        self.publish('users', UserHandler())
        self.publish('products', ProductHandler())
        self.publish('orders', OrderHandler())

# CLI: python myapp.py users add Alice
# CLI: python myapp.py products list
# HTTP: POST /users/add, POST /products/list
```

### 8. Custom HTTP Configuration
```python
from smpub.http import create_fastapi_app

app_publisher = MyApp()
fastapi_app = create_fastapi_app(
    app_publisher,
    title="My API",
    version="1.0.0",
    description="API description",
    docs_url="/api-docs"
)
```

### 9. API Schema Introspection
```python
class MyHandler:
    api = Switcher()
    # ... methods ...

handler = MyHandler()
# Get JSON schema of handler API
schema = handler.smpublisher.get_api_json()
# Returns: {"class": "MyHandler", "methods": {...}, "description": "..."}
```

### 10. Interactive Parameter Input
```python
# In CLI, use --interactive flag for form-based input
python myapp.py handler process --interactive
# Opens Textual form to input parameters interactively
```

## Critical Rules

1. **__slots__ requirement**: If handler uses `__slots__`, must include `'smpublisher'`
2. **Auto-upgrade**: Plain `Switcher` automatically upgraded to `ApiSwitcher` on publish
3. **Type hints**: Use type hints for automatic validation and OpenAPI generation
4. **Method naming**: With prefix, method `handler_add` → exposed as `add`
5. **HTTP methods**: All HTTP endpoints use POST (not GET)
6. **Context injection**: `smpublisher` attribute automatically injected by Publisher

## Common Anti-Patterns

❌ **Don't**: Forget `'smpublisher'` in `__slots__`
❌ **Don't**: Use handlers without `api = Switcher()`
❌ **Don't**: Mix sync code in async methods (breaks async contexts)

✅ **Do**: Use type hints on all method parameters
✅ **Do**: Add docstrings for OpenAPI descriptions
✅ **Do**: Use `cli`/`openapi` flags to control exposure

## Quick Troubleshooting

**"Cannot publish: class uses __slots__"**: Add `'smpublisher'` to your `__slots__` tuple
**"No such handler"**: Check handler name in `publish()` call
**"Validation error"**: Ensure CLI arguments match parameter types
**404 on HTTP endpoint**: Check `openapi=True` in publish call

## Run Modes

```python
# Auto-detect (CLI if args, HTTP otherwise)
app.run()

# Explicit CLI
app.run(mode="cli")

# Explicit HTTP
app.run(mode="http", port=8000)
```

## Advanced Features

### OpenAPI Schema Generation
```python
from smpub.http.openapi import generate_openapi_schema

schema = generate_openapi_schema(
    app,
    title="My API",
    version="1.0.0",
    description="Custom API"
)
# Returns full OpenAPI 3.0 spec
```

### Validation Control
```python
from smpub.validation import validate_args

# Validate CLI arguments against method signature
validated = validate_args(method, ["arg1", "arg2"])
# Returns: {"param1": "arg1", "param2": "arg2"} with type conversion
```

### Interactive Forms
```python
from smpub.interactive import prompt_for_parameters

# Prompt user for all method parameters
values = prompt_for_parameters(method)
# Returns list of string values from Textual form
```

## Version
Current: 0.2.0 (Python 3.10+)

## Performance
- Dispatch: ~2μs overhead (from SmartSwitch)
- Validation: Pydantic-based (microseconds for typical payloads)
- HTTP: FastAPI performance (async ASGI)

## Dependencies
- **smartswitch** >= 0.1.0 (rule-based dispatch)
- **pydantic** >= 2.0 (validation)
- **fastapi** >= 0.104.0 (optional, for HTTP mode)
- **textual** >= 0.41.0 (optional, for interactive mode)

## Related Projects
Part of [Genro-Libs toolkit](https://github.com/softwell/genro-libs)
- [smartswitch](https://github.com/genropy/smartswitch) - Function dispatch
- [smartasync](https://github.com/genropy/smartasync) - Async/sync compatibility
- [gtext](https://github.com/genropy/gtext) - Text transformation

## Quick Examples by Use Case

### Use Case: REST API
```python
class API(Publisher):
    def initialize(self):
        self.publish('users', UserHandler(), http_path="/api/users")
        self.publish('auth', AuthHandler(), http_path="/api/auth")

API().run(mode="http")  # OpenAPI + Swagger at /docs
```

### Use Case: CLI Tool
```python
class CLI(Publisher):
    def initialize(self):
        self.publish('db', DatabaseHandler(), openapi=False)
        self.publish('cache', CacheHandler(), openapi=False)

CLI().run()  # Pure CLI, no HTTP
```

### Use Case: Dual CLI/API
```python
class DualApp(Publisher):
    def initialize(self):
        # Same handlers for both CLI and HTTP
        self.publish('data', DataHandler())

# CLI: python app.py data import file.csv
# HTTP: POST /data/import with {"file": "file.csv"}
```

## Full Example - Real Application
```python
from smpub import Publisher
from smartswitch import Switcher
from typing import List

class UserService:
    __slots__ = ('users', 'smpublisher')
    api = Switcher(prefix='user_')

    def __init__(self):
        self.users = {}

    @api
    def user_create(self, username: str, email: str, age: int = 18):
        """Create a new user."""
        self.users[username] = {'email': email, 'age': age}
        return f"Created user {username}"

    @api
    def user_list(self) -> List[str]:
        """List all usernames."""
        return list(self.users.keys())

    @api
    def user_get(self, username: str):
        """Get user details."""
        return self.users.get(username, "Not found")

    @api
    async def user_fetch_remote(self, username: str):
        """Fetch user from remote API (async)."""
        # Async HTTP call here
        return {"username": username, "remote": True}

class UserApp(Publisher):
    def initialize(self):
        self.users = UserService()
        self.publish('users', self.users, http_path="/api/v1/users")

if __name__ == "__main__":
    app = UserApp()

    # CLI usage:
    # python app.py users create alice alice@example.com 25
    # python app.py users list
    # python app.py users get alice

    # HTTP usage:
    # app.run(mode="http")
    # Then: POST /api/v1/users/create {"username": "alice", "email": "...", "age": 25}

    app.run()  # Auto-detect mode
```
