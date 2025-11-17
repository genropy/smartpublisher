# SmartPublisher - New Architecture (Skeleton)

This directory contains a **skeleton implementation** of the new SmartPublisher architecture based on the design discussion.

## Purpose

This is a **proof-of-concept** to demonstrate the new architecture. It is NOT production-ready, but shows the structure and principles.

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `publisher.py` | Minimal Publisher class (orchestration only) | ~80 |
| `system_commands.py` | Business logic for Publisher introspection | ~90 |
| `output_formatter.py` | Format structured data at edge | ~120 |
| `channels/cli.py` | CLI channel with `cli_api` Switcher | ~180 |
| `channels/http.py` | HTTP channel with `http_api` Switcher | ~220 |
| `example_app.py` | Complete working example | ~350 |
| `ARCHITECTURE.md` | Detailed architecture documentation | ~600 |

**Total: ~1640 lines** (vs old Publisher.py: 416 lines that did everything)

## Quick Start

### 1. See the Example

```bash
cd src_new
python example_app.py
```

This runs all examples showing:
- CLI channel usage
- HTTP channel usage
- Two-level command structure
- Single source of truth principle

### 2. Read the Architecture

Open `ARCHITECTURE.md` for detailed explanation of:
- Core principles
- Architecture diagram
- Two-level command system
- Comparison with old architecture

### 3. Explore the Code

**Suggested reading order:**
1. `publisher.py` - Start here, see how minimal it is
2. `system_commands.py` - Business logic for introspection
3. `channels/cli.py` - CLI channel implementation
4. `channels/http.py` - HTTP channel implementation
5. `output_formatter.py` - Formatting at the edge
6. `example_app.py` - See it all working together

## Core Principles

### 1. Publisher is MINIMAL

```python
class Publisher:
    """Orchestration only - NO transport code."""

    def __init__(self):
        self.api = Switcher(name="root").plug("pydantic")
        self._init_system_commands()
        self.on_init()

    def publish(self, name, handler):
        """Returns structured data - NO print!"""
        return {"status": "published", "name": name}
```

**~80 lines total** - just orchestration, no CLI/HTTP code.

### 2. Each Channel is Separate

```python
# CLI channel
class PublisherCLI:
    cli_api = Switcher(name="cli")  # CLI-specific commands

    @cli_api
    def help(self) -> dict:
        """Auto-generated from Switcher."""
        return self.publisher.api.get_api_json()

# HTTP channel
class PublisherHTTP:
    http_api = Switcher(name="http")  # HTTP-specific commands

    @http_api
    def health(self) -> dict:
        """Health check endpoint."""
        return {"status": "healthy"}
```

Each channel has **its own Switcher** for transport-specific utilities.

### 3. Two-Level Commands

**Level 1: Business Commands** (channel-agnostic)
```python
class ShopHandler:
    api = Switcher(name="shop")

    @api
    def list(self) -> dict:
        """Works on ALL channels."""
        return {"products": [...]}
```

**Level 2: Channel Commands** (transport-specific)
```python
# CLI utilities
cli.cli_api['help']()      # CLI-specific
cli.cli_api['version']()   # CLI-specific

# HTTP utilities
http.http_api['health']()        # HTTP-specific
http.http_api['openapi_schema']()  # HTTP-specific
```

### 4. NO Print Statements in Business Logic

```python
# ❌ OLD (BAD)
def list(self):
    print("Products:")
    for product in products:
        print(f"  - {product}")

# ✅ NEW (GOOD)
def list(self) -> dict:
    return {"products": products}  # Structured data

# Print only at edge
cli.run()  # Prints formatted output here
```

### 5. Single Source of Truth

```python
# All commands in Switcher → Auto-generated everything
api_schema = publisher.api.get_api_json()

# CLI help is auto-generated
help_text = formatter.format_help(api_schema)

# OpenAPI is auto-generated
openapi_spec = http.http_api['openapi_schema']()

# Future: WSDL auto-generated from same source
```

## Architecture Comparison

### Old Architecture (416 lines)

```python
class Publisher:
    def __init__(self): ...
    def publish(self): ...
    def _run_cli(self):         # 200+ lines, many prints
    def _run_http(self):        # 150+ lines
    def _print_cli_help(self):  # Manual help
    def _print_handler_help(self): ...
    # ... many more methods
```

**Problems:**
- Everything in one class
- Print statements everywhere
- Manual help generation (duplication)
- Hard to extend (add SOAP? modify Publisher!)

### New Architecture (~1640 lines total, separated)

```python
# publisher.py (~80 lines)
class Publisher:
    """Orchestration only."""
    def __init__(self): ...
    def publish(self): ...

# channels/cli.py (~180 lines)
class PublisherCLI:
    """CLI channel with cli_api Switcher."""
    cli_api = Switcher(name="cli")
    @cli_api
    def help(self): ...

# channels/http.py (~220 lines)
class PublisherHTTP:
    """HTTP channel with http_api Switcher."""
    http_api = Switcher(name="http")
    @http_api
    def health(self): ...
```

**Benefits:**
- Clean separation of concerns
- NO print statements in business logic
- Auto-generated help (no duplication)
- Easy to extend (add SOAP? create PublisherSOAP!)
- Each part is independently testable

## Runtime Channel Configuration

Channels can be enabled/disabled at runtime:

```bash
# Register app
smpub add myapp /path/to/app

# Enable channels (runtime)
smpub myapp enable cli
smpub myapp enable http --port 8000

# Disable channels
smpub myapp disable cli

# List enabled channels
smpub myapp channels
```

Registry stores configuration:

```json
{
  "apps": {
    "myapp": {
      "path": "/path/to/app",
      "channels": {
        "cli": {"enabled": true},
        "http": {"enabled": true, "port": 8000}
      }
    }
  }
}
```

## Extending with New Channels

Adding new channels is trivial:

```python
# Add SOAP channel
class PublisherSOAP:
    """SOAP channel."""

    soap_api = Switcher(name="soap")

    def __init__(self, publisher):
        self.publisher = publisher

    @soap_api
    def wsdl(self) -> dict:
        """Generate WSDL from publisher.api."""
        api_schema = self.publisher.api.get_api_json()
        # Convert to WSDL format
        return {...}

    def create_soap_server(self):
        """Create SOAP server wrapping publisher.api."""
        # Use spyne or similar
        pass

# Add WebSocket channel
class PublisherWebSocket:
    """WebSocket channel."""

    ws_api = Switcher(name="websocket")

    @ws_api
    def broadcast(self, message: dict) -> dict:
        """Broadcast to all clients."""
        return {"sent": True}

    async def handle_connection(self, websocket):
        """Handle WebSocket connection."""
        # Dispatch to publisher.api
        pass
```

**NO CHANGES to Publisher required!**

## Testing Strategy

Each layer is independently testable:

```python
# Test business logic (no transport)
def test_shop_list():
    shop = ShopHandler()
    result = shop.list()
    assert "products" in result
    assert len(result["products"]) > 0

# Test Publisher orchestration
def test_publisher_publish():
    publisher = ShopApp()
    assert "shop" in publisher.published_instances

# Test CLI channel
def test_cli_help():
    publisher = ShopApp()
    cli = PublisherCLI(publisher)
    result = cli.cli_api['help']()
    assert "handlers" in result

# Test HTTP channel
def test_http_health():
    publisher = ShopApp()
    http = PublisherHTTP(publisher)
    result = http.http_api['health']()
    assert result["status"] == "healthy"
```

## Migration Path

1. **Phase 1**: Keep old code, add `src_new/` alongside
2. **Phase 2**: Migrate handlers to new pattern (return structured data)
3. **Phase 3**: Create PublisherCLI for CLI
4. **Phase 4**: Create PublisherHTTP for HTTP
5. **Phase 5**: Update `cli.py` to use new channels
6. **Phase 6**: Remove old Publisher class

## Next Steps

To make this production-ready:

1. **Argument Parsing**: Implement full CLI argument parsing in PublisherCLI
2. **Validation**: Integrate Pydantic validation
3. **Error Handling**: Comprehensive error handling
4. **FastAPI Integration**: Complete HTTP implementation
5. **Registry Integration**: Connect with smpub CLI registry
6. **Tests**: Full test suite
7. **Documentation**: API reference and user guide

## Questions?

See `ARCHITECTURE.md` for detailed explanations and comparisons.

---

**Summary**: This skeleton shows how to build SmartPublisher with clean separation, no print statements in business logic, and easy extensibility for new channels. The total code is larger (~1640 lines) but each part is focused and testable, vs 416 lines of mixed concerns in old Publisher.
