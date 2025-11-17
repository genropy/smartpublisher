# smpub Documentation

Welcome to the smpub documentation!

## Getting Started

- **[Publishing Guide](publishing-guide.md)** - Complete tutorial on how to expose your library with smpub
  - Handler requirements
  - Best practices
  - Common patterns
  - Complete examples

## Core Concepts

### Architecture

See the [Architecture section](../README.md#architecture) in the main README for:
- Layered architecture diagram
- Component descriptions
- Integration between layers

### Key Components

- **Publisher** - Base class for applications
- **PublishedClass** - Mixin for handlers (optional)
- **PublisherContext** - Context object injected into handlers
- **Validation Layer** - Pydantic-based type validation
- **Interactive Layer** - dialog-based parameter prompting

## Features

### Type Validation with Pydantic

Automatic parameter validation and type conversion:
- String → int, float, bool conversion
- Clear error messages
- Default value support

See [Type Validation](../README.md#type-validation-with-pydantic) for examples.

### Interactive Mode

User-friendly parameter prompting with dialog:
- Type-aware prompts
- Default value display
- Boolean choice menus

See [Interactive Mode](../README.md#interactive-mode-with-dialog) for details.

## API Reference

### Publisher

```python
from smartpublisher import Publisher

class MyApp(Publisher):
    def initialize(self):
        # Called automatically
        handler = MyHandler()
        self.publish('name', handler, cli=True, openapi=True)
```

**Methods:**
- `publish(name, handler, cli=True, openapi=True, ...)` - Register handler
- `run(mode=None, port=8000)` - Run application (auto-detects mode)

### PublishedClass

```python
from smartpublisher import PublishedClass
from smartroute import Router, route

class MyHandler(PublishedClass):
    __slots__ = ('data',)  # Your slots
    api = Router(name='my')

    @api
    def my_method(self, param: int) -> str:
        # Access publisher context
        schema = self.publisher.get_api_json()
        return f"Result: {param}"
```

**Attributes:**
- `publisher: PublisherContext` - Injected context object

### PublisherContext

Available via `handler.publisher`:

**Methods:**
- `get_api_json(target=None, recursive=False)` - Extract API schema

## Examples

Check the [examples/](../examples/) directory for working code:

- `test_params.py` - Simple handler with various parameter types
- `sample_app/` - Multi-handler application example

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=smpub --cov-report=html

# Specific test file
pytest tests/test_validation.py -v
```

Test files:
- `tests/test_validation.py` - Pydantic validation tests
- `tests/test_interactive.py` - dialog integration tests
- `tests/test_publisher.py` - Publisher/Handler tests

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Links

- [GitHub Repository](https://github.com/genropy/smartpublisher)
- [Issue Tracker](https://github.com/genropy/smartpublisher/issues)
- [PyPI Package](https://pypi.org/project/smartpublisher/)
- [Genro-Libs Toolkit](https://github.com/softwell/genro-libs)

---

**License**: MIT | **Author**: Genropy Team
