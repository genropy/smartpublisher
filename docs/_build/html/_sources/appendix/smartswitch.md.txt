# Integration with SmartSwitch

smpub is built on top of [SmartSwitch](https://github.com/genropy/smartswitch), leveraging its powerful rule-based function dispatch.

## How smpub Uses SmartSwitch

### Parent-Child API Structure

smpub creates a hierarchical API structure using SmartSwitch's parent-child relationships:

```text
Publisher                    # Your app
  └─ parent_api (Switcher)  # Root API
      └─ Handler.api         # Handler API (child)
          └─ methods         # Individual methods
```

**Example**:

```python
class MyApp(Publisher):
    def initialize(self):
        handler = MyHandler()
        self.publish('myhandler', handler)
        # Now: MyHandler.api.parent = MyApp.parent_api
```

### Method Dispatch

All method calls go through SmartSwitch:

1. **CLI**: `smpub myapp handler method args`
   - Registry loads app
   - Publisher finds handler by name
   - Handler's Switcher finds method by name
   - Method executes with validated args

2. **HTTP**: `POST /handler/method`
   - FastAPI routes to handler
   - Handler's Switcher finds method
   - Method executes with validated params

## Switcher Configuration

### Handler API Definition

Handlers define their API using SmartSwitch `Switcher`:

```python
from smartswitch import Switcher

class MyHandler(PublishedClass):
    api = Switcher(prefix='my_')

    @api
    def my_method(self, param: str):
        """Method with prefix."""
        pass
```

**Prefix Convention**:
- Avoids naming conflicts
- Groups related methods
- Clear method ownership

### Method Decoration

The `@api` decorator registers methods with SmartSwitch:

```python
@api
def my_create(self, name: str) -> dict:
    """Create something."""
    return {"name": name, "id": 1}

@api
def my_delete(self, id: int) -> bool:
    """Delete something."""
    return True
```

SmartSwitch tracks:
- Method name (with prefix stripped for display)
- Parameters and types
- Return type
- Docstring

## API Discovery

### get_api_json()

smpub provides `get_api_json()` through PublisherContext:

```python
@api
def my_info(self) -> dict:
    # Get API schema for this handler
    schema = self.publisher.get_api_json()

    return {
        "class": schema['class'],
        "methods": list(schema['methods'].keys())
    }
```

**Schema Structure**:

```python
{
    "class": "MyHandler",
    "methods": {
        "create": {
            "full_name": "my_create",
            "docstring": "Create something.",
            "description": "Create something.",
            "parameters": [
                {
                    "name": "name",
                    "type": "str",
                    "required": True,
                    "default": None
                }
            ],
            "return_type": "dict"
        },
        # ... more methods
    }
}
```

### Use Cases

1. **Help Generation**: CLI help text from schema
2. **OpenAPI Schema**: HTTP endpoints from schema
3. **Introspection**: Runtime API discovery
4. **Documentation**: Auto-generated docs

## SmartSwitch Features Not Used

smpub uses SmartSwitch primarily for:
- Method registration (`@api`)
- Name-based dispatch
- Parent-child relationships
- API introspection

smpub does **not** currently use:
- **Value rules**: Type-based dispatch
- **Type rules**: Pattern matching
- **Custom rules**: Complex dispatch logic

These features are available if you need them in handlers:

```python
from smartswitch import Switcher, ValRule

class AdvancedHandler(PublishedClass):
    api = Switcher(prefix='adv_')

    @api
    def adv_process(self, data):
        """Process data (dispatches by type)."""
        pass

    @api
    @ValRule(type(data) == str)
    def adv_process(self, data: str):
        """Process string data."""
        return f"String: {data}"

    @api
    @ValRule(type(data) == dict)
    def adv_process(self, data: dict):
        """Process dict data."""
        return f"Dict: {len(data)} keys"
```

## Benefits of SmartSwitch Foundation

### 1. Clean Method Registration

```python
# Without SmartSwitch (manual)
class Handler:
    def __init__(self):
        self._methods = {
            'create': self.my_create,
            'delete': self.my_delete
        }

# With SmartSwitch (declarative)
class Handler(PublishedClass):
    api = Switcher(prefix='my_')

    @api
    def my_create(self, ...): pass

    @api
    def my_delete(self, ...): pass
```

### 2. Automatic Discovery

SmartSwitch tracks all decorated methods automatically:

```python
# Get all API methods
methods = handler.__class__.api.get_methods()

# Get method metadata
info = handler.__class__.api.get_method_info('create')
```

### 3. Hierarchical APIs

Parent-child relationships enable nested APIs:

```text
# Root API
app.parent_api
    └─ users.api        # /users/*
    └─ posts.api        # /posts/*
    └─ comments.api     # /comments/*
```

### 4. Type Safety

SmartSwitch preserves type hints:

```python
@api
def my_method(self, count: int) -> list:
    pass

# SmartSwitch knows: int → list
# Pydantic validates: "10" → int(10)
```

## Comparison with Direct Use

### Using SmartSwitch Directly

```python
from smartswitch import Switcher

api = Switcher()

@api
def process(data: str):
    return f"Processing: {data}"

# Call directly
result = api.process("hello")
```

### Using smpub (SmartSwitch + More)

```python
from smpub import Publisher, PublishedClass
from smartswitch import Switcher

class MyHandler(PublishedClass):
    api = Switcher(prefix='my_')

    @api
    def my_process(self, data: str):
        return f"Processing: {data}"

class MyApp(Publisher):
    def initialize(self):
        self.handler = MyHandler()
        self.publish('handler', self.handler, cli=True, openapi=True)

# Use via CLI
# $ smpub add myapp --path .
# $ smpub myapp handler process "hello"

# Use via HTTP
# POST /handler/process {"data": "hello"}
```

**smpub adds**:
- CLI argument parsing
- Pydantic validation
- Interactive mode
- FastAPI integration
- Help generation
- Registry system

## Further Reading

- [SmartSwitch Documentation](https://smartswitch.readthedocs.io)
- [SmartSwitch GitHub](https://github.com/genropy/smartswitch)
- [Publisher Class](../api/publisher.md)
- [Handler Classes](../guide/handlers.md)
