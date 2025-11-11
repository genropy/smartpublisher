# Architecture

## Overview

smpub follows a clean layered architecture that separates concerns and provides flexibility in how applications are exposed.

## Layered Architecture

```mermaid
graph TB
    App["Your Application<br/>(inherits from Publisher)"]
    Publisher["Publisher Layer<br/>• parent_api (root Switcher)<br/>• CLI/OpenAPI exposure control<br/>• Argument validation (Pydantic)<br/>• Interactive mode support (Textual)<br/>• HTTP server (FastAPI)"]
    Handlers["Handler Instances<br/>(inherit from PublishedClass)<br/>• api = ApiSwitcher(prefix='...')<br/>• publisher: PublisherContext<br/>• Business logic methods"]
    ApiSwitcher["ApiSwitcher<br/>• Extends SmartSwitch Switcher<br/>• Creates Pydantic models at decoration time<br/>• Enables OpenAPI schema generation"]
    SmartSwitch["SmartSwitch Core<br/>• Parent-child relationships<br/>• Method dispatch by name/rules<br/>• Hierarchical API navigation"]

    App -->|"initialize() / publish()"| Publisher
    Publisher -->|"publishes to"| Handlers
    Handlers -->|"uses"| ApiSwitcher
    ApiSwitcher -->|"extends"| SmartSwitch

    style App fill:#e1f5ff
    style Publisher fill:#fff4e1
    style Handlers fill:#e8f5e9
    style ApiSwitcher fill:#ffe0b2
    style SmartSwitch fill:#f3e5f5
```

## Core Components

### Publisher

**Role**: Application orchestrator

**Responsibilities**:
- Register handlers with `publish()`
- Control CLI/OpenAPI exposure
- Create root Switcher (`parent_api`)
- Inject PublisherContext into handlers
- Run CLI or HTTP mode

**Key Methods**:
- `__init__()` - Creates parent_api, calls initialize()
- `initialize()` - Subclass hook for handler registration
- `publish()` - Register handler with exposure control
- `run()` - Auto-detect or explicit mode selection
- `_run_cli()` - CLI execution with Pydantic validation
- `_run_http()` - FastAPI server with Swagger UI

### PublishedClass

**Role**: Handler base class (mixin)

**Responsibilities**:
- Provide `publisher` slot for context injection
- Allow handlers to use `__slots__` for memory efficiency

**Usage**:

```python
from smpub.apiswitcher import ApiSwitcher

class MyHandler(PublishedClass):
    __slots__ = ('data',)  # Your slots
    api = ApiSwitcher(prefix='my_')  # Use ApiSwitcher for HTTP support

    # publisher slot provided by PublishedClass
```

**Note**: For HTTP/OpenAPI exposure, handlers must use `ApiSwitcher` instead of plain `Switcher`. See [ApiSwitcher](#apiswitcher) section for details.

### PublisherContext

**Role**: Context object injected into handlers

**Responsibilities**:
- Provide access to publisher functionality
- Enable API introspection

**Key Methods**:
- `get_api_json()` - Extract API schema for handler

**Access Pattern**:
```python
@api
def my_method(self):
    # Access publisher context
    schema = self.publisher.get_api_json()
```

### ApiSwitcher

**Role**: Enhanced Switcher with OpenAPI support

**Problem Solved**:
When using standard `Switcher` with FastAPI, the OpenAPI schema doesn't show method parameters because FastAPI relies on introspection of Pydantic models at **app creation time**. Creating models dynamically at runtime results in invisible parameters in Swagger UI.

**Solution**:
`ApiSwitcher` creates Pydantic models at **decoration time** (when the class is defined), making them available for FastAPI's introspection during app creation.

**Key Features**:

- Extends `smartswitch.Switcher`
- Creates Pydantic models when methods are decorated
- Stores models in `_pydantic_models` dict
- Required for HTTP/OpenAPI exposure

**Responsibilities**:

- Create Pydantic model for each decorated method
- Handle type conversions (Literal → Enum for Pydantic)
- Store models for retrieval by FastAPI integration
- Provide `get_pydantic_model(method_name)` for model access

**Usage**:
```python
from smpub.apiswitcher import ApiSwitcher

class MyHandler(PublishedClass):
    api = ApiSwitcher(prefix='my_')  # Required for HTTP mode

    @api
    def my_method(self, name: str, age: int) -> str:
        """Method with automatic Pydantic model creation."""
        return f"{name} is {age} years old"
```

**Model Creation Process**:

1. Method decorated with `@api`
2. ApiSwitcher introspects method signature
3. Creates Pydantic model from type hints
4. Stores model in `_pydantic_models[method_name]`
5. Model available for FastAPI at app creation time

**Type Support**:

- Basic types: `str`, `int`, `float`, `bool`
- Optional types with defaults
- `Literal` types (converted to Enum)
- Complex types (list, dict, etc.)

**Requirement**:

When using HTTP mode (`smpub <app> serve`), handlers **must** use `ApiSwitcher` instead of plain `Switcher`. If not, a `TypeError` is raised with a clear message.

## Data Flow

### CLI Mode Flow

```mermaid
graph LR
    CLI[Command Line] --> Parse[Parse: handler method args]
    Parse --> Interactive{Interactive?}
    Interactive -->|Yes| Textual[Textual TUI form]
    Interactive -->|No| Pydantic[Pydantic validation]
    Textual --> Pydantic
    Pydantic --> Dispatch[SmartSwitch dispatch]
    Dispatch --> Method[Execute method]
    Method --> Result[Print result]

    style CLI fill:#e3f2fd
    style Method fill:#c8e6c9
    style Result fill:#fff9c4
```

### HTTP Mode Flow

```mermaid
graph LR
    HTTP[HTTP Request] --> FastAPI[FastAPI routing]
    FastAPI --> JSON[Parse JSON body]
    JSON --> Pydantic[Pydantic validation]
    Pydantic --> Dispatch[SmartSwitch dispatch]
    Dispatch --> Method[Execute method]
    Method --> Response["JSON response<br/>{status: success, result: ...}"]

    style HTTP fill:#e3f2fd
    style Method fill:#c8e6c9
    style Response fill:#fff9c4
```

## Validation Layer

### Pydantic Integration

smpub uses Pydantic v2 for automatic parameter validation:

1. **Model Generation**: Create Pydantic model from method signature
2. **Type Conversion**: Convert CLI strings to proper types
3. **Validation**: Validate all parameters
4. **Error Handling**: Format validation errors for user

**Supported Types**:
- `str` - String values
- `int` - Integer with parsing
- `float` - Floating-point with parsing
- `bool` - Boolean with "True"/"False" parsing
- Optional with defaults

**Example**:
```python
@api
def add(self, a: int, b: int) -> int:
    return a + b

# CLI: "10" "20" → int(10) + int(20) → 30
```

## Interactive Layer

### Textual Integration

Optional layer for user-friendly parameter input using Textual TUI framework:

1. **Type-aware Prompts**: Different input widgets for different types
2. **Default Display**: Show default values in forms
3. **Boolean Choices**: Checkbox or switch for bool params
4. **Validation**: Real-time validation with visual feedback
5. **Rich UI**: Modern terminal UI with colors and interactive elements

**Flow**:

```mermaid
graph TB
    Start[--interactive flag] --> Check{Textual available?}
    Check -->|No| Error[Error: Textual not installed]
    Check -->|Yes| App[Launch Textual app]
    App --> Form[Display parameter form]
    Form --> Input[User fills parameters]
    Input --> Validate[Real-time validation]
    Validate --> Invalid{Valid?}
    Invalid -->|No| Error2[Show validation errors]
    Error2 --> Input
    Invalid -->|Yes| Submit[User submits form]
    Submit --> Execute[Execute method]
    Execute --> Result[Show result in UI]

    style Start fill:#e3f2fd
    style Error fill:#ffcdd2
    style Error2 fill:#ffcdd2
    style Execute fill:#c8e6c9
    style Result fill:#fff9c4
```

## HTTP Layer

### FastAPI Integration

HTTP mode creates a FastAPI app dynamically:

1. **App Creation**: Generate FastAPI app from publisher
2. **Route Generation**: POST endpoint for each method
3. **Validation**: Use existing Pydantic validation
4. **OpenAPI**: Automatic schema generation
5. **Swagger UI**: Interactive documentation at `/docs`

**Endpoint Pattern**:

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Handler
    participant Method

    Client->>FastAPI: POST /{handler}/{method}
    Note over Client,FastAPI: Body: {"param1": value1, "param2": value2}
    FastAPI->>FastAPI: Pydantic validation
    FastAPI->>Handler: Dispatch to handler
    Handler->>Method: Call method(param1, param2)
    Method-->>Handler: Return result
    Handler-->>FastAPI: result
    FastAPI-->>Client: {"status": "success", "result": ...}
```

### CLI Command: `smpub <app> serve`

The `serve` command provides an easy way to start the HTTP server from the command line:

**Syntax**:
```bash
smpub <appname> serve [port]
```

**Default Port**: 8000

**Example**:
```bash
# Start on default port 8000
smpub mailapp serve

# Start on custom port
smpub mailapp serve 8084
```

**Flow**:

```mermaid
graph LR
    CLI[smpub mailapp serve 8084] --> Parse[Parse command]
    Parse --> Load[Load app from registry]
    Load --> Check{ApiSwitcher?}
    Check -->|No| Error[TypeError: Handlers must use ApiSwitcher]
    Check -->|Yes| Create[Create FastAPI app]
    Create --> Routes[Generate routes from handlers]
    Routes --> Home[Add homepage with links]
    Home --> Start[Start uvicorn on port 8084]
    Start --> Ready[Server ready]

    style CLI fill:#e3f2fd
    style Error fill:#ffcdd2
    style Ready fill:#c8e6c9
```

**Available Endpoints**:

- `/` - Homepage with links to documentation
- `/docs` - Swagger UI (interactive API testing)
- `/redoc` - ReDoc (alternative documentation)
- `/openapi.json` - OpenAPI schema
- `/{handler}/{method}` - API endpoints (POST)

**Homepage Features**:

The homepage provides a user-friendly entry point with:

- Application name and description
- Clickable links to Swagger UI and ReDoc
- Link to download OpenAPI JSON schema
- Modern HTML design with styling
- Easy navigation for developers

## Registry System

### Local Registry (`.published`)

Project-specific app registry:
- JSON file in project directory
- Maps app names to paths
- Used by `smpub` CLI

### Global Registry (`~/.smartlibs/publisher/registry.json`)

System-wide app registry:
- JSON file in home directory
- Global app access
- Shared across projects

## Design Principles

### 1. Separation of Concerns

- **Handlers**: Business logic only
- **Publisher**: Orchestration and exposure
- **Validation**: Separate Pydantic layer
- **Interactive**: Optional Textual TUI layer
- **HTTP**: Separate FastAPI layer
- **ApiSwitcher**: Decoration-time Pydantic model creation

### 2. Convention over Configuration

- Auto-detect CLI vs HTTP mode
- Automatic Pydantic model generation
- Automatic route generation
- Standard prefix patterns

### 3. Progressive Enhancement

- Core: CLI with basic arguments
- +Pydantic: Type validation
- +Textual: Interactive TUI mode
- +ApiSwitcher: OpenAPI schema support
- +FastAPI: HTTP/API mode
- Each layer is optional (except ApiSwitcher when using HTTP)

### 4. SmartSwitch Foundation

- All dispatch goes through SmartSwitch
- Parent-child relationships for hierarchy
- Consistent API structure
- Rule-based method selection

## Extension Points

### Custom Validators

Add custom Pydantic validators:

```python
from pydantic import validator

@api
def my_method(self, email: str):
    # Pydantic will validate
    pass
```

### Custom Routes

Override route generation:

```python
from smpub.http import create_fastapi_app

app = create_fastapi_app(publisher)
# Add custom routes
app.get("/health")(lambda: {"status": "ok"})
```

### Custom Interactive Forms

Extend interactive module with custom Textual widgets:

```python
from smpub.interactive import InteractiveApp
from textual.widgets import Input, Button

# Create custom Textual app
class CustomInteractiveApp(InteractiveApp):
    def create_form(self):
        # Custom form logic with Textual widgets
        pass
```

## Performance Considerations

### Memory

- Use `__slots__` in handlers (PublishedClass provides publisher slot)
- Handlers are singleton instances per publisher

### Validation

- Pydantic models cached per method
- Validation happens once per invocation
- Type conversion is fast (native Python)

### HTTP

- FastAPI is async-capable (though handlers are sync)
- Uvicorn with standard extensions for production
- Each request validated independently

## Future Architecture

### Planned Enhancements

1. **Async Handlers**: Support for async methods
2. **WebSocket Support**: Real-time endpoints
3. **Plugin System**: Custom validation/transformation
4. **Multi-Handler Routes**: Compose multiple handlers
5. **GraphQL**: Alternative to REST API

### Compatibility

- Backward compatible within major versions
- SmartSwitch upgrades tracked
- Pydantic v2 required (v1 not supported)
