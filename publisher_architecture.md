# SmartPublisher Architecture

**Version**: 0.3.0 (with autocompletion system)
**Last Updated**: 2025-11-18

## Core Principle: Publisher is a Published App

**Key insight**: Publisher is not a special meta-object outside the ecosystem. Publisher is a **normal app** with a specific task (publishing other apps) and commands to execute that task.

Therefore: **Publisher IS a PublishedClass**.

## Entry Point Architecture

Publisher is the **primary module** for CLI entry. The flow is:

1. Shell executes `smpub` command
2. Pip invokes `smartpublisher.publisher:main` (module-level function)
3. `main()` creates `Publisher()` instance
4. Calls `publisher.run_cli()` (instance method)
5. Which delegates to CLI channel: `cli_channel.run(args)`

**Key point**: `cli_channel.py` is an **auxiliary module** (the CLI channel implementation), not the entry point.

### Entry Point Code

```python
# publisher.py
def main():
    """Entry point for smpub command."""
    publisher = Publisher()
    publisher.run_cli()

# pyproject.toml
[project.scripts]
smpub = "smartpublisher.publisher:main"
```

## Inheritance Structure

```python
class Publisher(PublishedClass):
    """
    Publisher is a PublishedClass (not just RoutedClass).
    It's an app like any other, but it's the root app.
    """

    # Inherits api = Router from PublishedClass
```

**What Publisher inherits from PublishedClass**:
- Router `api` with pydantic plugin
- `_system` commands (list_handlers, get_handler_info, get_api_tree)
- `published_instances` dictionary
- Automatic help via `api.describe()`
- Lifecycle hooks infrastructure
- `publish()` method

## Initialization Pattern

```python
def __init__(self, registry_path: Path = None, use_global: bool = False):
    super().__init__()  # Initialize PublishedClass

    # Core registries
    self.app_registry = AppRegistry(self, registry_path=registry_path, use_global=use_global)

    # Track loaded applications
    self.applications: dict[str, PublishedClass] = {}

    # Channel registry / instances
    self.chan_registry = ChanRegistry(self)
    self.chan_registry = ChanRegistry(self)

    # Publish registry handlers for CLI exposure
    self.publish("apps", self.app_registry)
    self.publish("chan", self.chan_registry)
```

**Key changes from previous version**:
- Uses `self.publish()` instead of `self.api.add_child()`
- Adds handlers to both `published_instances` dict and Router hierarchy
- Maintains `applications` dict for tracking

## Registry Structure

### Paths

- **Local registry**: `.published` (file, not directory - current directory)
- **Global registry**: `~/.smartlibs/publisher/registry.json` (home directory)

Changed from previous `.smpub/` structure to align with smartlibs conventions.

### AppRegistry

```python
class AppRegistry(RoutedClass):
    api = Router(name="apps")

    def __init__(self, publisher, registry_path=None, use_global=False):
        self._publisher = publisher
        # ... auto-initialize registry
```

**Methods** (exposed via Router):
- `add(name, path, module, class_name)` - Register app
- `remove(name)` - Unregister app
- `list()` - List registered apps
- `getapp(name)` - Get app info
- `load(name)` - Load app instance (internal)
- `unload(name)` - Unload app instance (internal)

### ChanRegistry

```python
class ChanRegistry(RoutedClass):
    api = Router(name="channels")

    def __init__(self, publisher):
        self._publisher = publisher
        self.chan_registry = ChanRegistry(self)
        # ... autodiscover channels
```

**Autodiscovery**: Scans `channels/` directory and instantiates:
- `CLIChannel` → registered as `'cli'`
- `PublisherHTTP` → registered as `'http'`

## Router Hierarchy

The complete Router tree structure:

```
Publisher.api (root)
├── apps (AppRegistry.api)
│   ├── add
│   ├── remove
│   ├── list
│   └── getapp
├── chan (ChanRegistry.api)
│   └── (channel methods, TBD)
└── _system (SystemCommands.api)
    ├── list_handlers
    ├── get_handler_info
    └── get_api_tree
```

**Accessing via Router**:
```python
publisher.api.get("apps")      # Returns AppRegistry instance
publisher.api.get("apps.list") # Returns list method
```

**Accessing via published_instances**:
```python
publisher.published_instances["apps"]     # AppRegistry instance
publisher.published_instances["chan"]     # ChanRegistry instance
publisher.published_instances["_system"]  # SystemCommands instance
```

## Channel Architecture

### CLIChannel

Located in `channels/cli_channel.py`:

```python
class CLIChannel(RoutedClass):
    cli_api = Router(name="cli")

    def __init__(self, publisher):
        self.publisher = publisher
        self.formatter = OutputFormatter()

    def run(self, args: list = None):
        """Main entry point for CLI execution."""
        # Handle completion requests
        if args and args[0] == '--complete':
            self._handle_completion(args[1:])
            return

        # Handle help
        if not args or args[0] in ['--help', '-h']:
            self._show_general_help()
            return

        # Route commands
        # ...
```

**Responsibilities**:
1. Parse command-line arguments
2. Handle completion requests (shell integration)
3. Route commands to handlers via Router
4. Format and display output
5. Handle errors

### Command Routing

```bash
# Direct publisher commands (implicit .self)
smpub serve http           # → publisher.serve('http')
smpub quit                 # → publisher.quit()

# Registry commands
smpub apps list            # → publisher.published_instances['apps'].list()
smpub apps add myapp ...   # → publisher.published_instances['apps'].add(...)

# System commands
smpub _system list_handlers  # → publisher.published_instances['_system'].list_handlers()
```

## Autocompletion System

### Overview

SmartPublisher implements a **dynamic, shell-agnostic completion system** that:
- Uses Router introspection (`api.describe()`)
- Supports bash, zsh, fish
- Provides hierarchical suggestions
- Includes inline hints (parameter signatures)

### Protocol

```bash
smpub --complete <shell> [cursor] <tokens...>
```

**Examples**:
```bash
smpub --complete bash 0 ""           # Suggest handlers
smpub --complete bash 0 "ap"         # Partial match → "apps"
smpub --complete bash 0 "apps" ""    # Suggest methods of apps
smpub --complete bash 0 "apps" "add" "" # Suggest parameters
```

### Response Format

JSON payload with structured suggestions:

```json
{
  "shell": "bash",
  "cursor": 0,
  "current_fragment": "ap",
  "completed_tokens": [],
  "suggestions": [
    {
      "type": "handler",
      "value": "apps",
      "display": "apps",
      "description": "Registry for managing Published applications...",
      "inline_hint": ""
    }
  ]
}
```

**Suggestion types**:
- `handler` - Top-level handlers (apps, chan, _system)
- `method` - Handler methods
- `system` - System commands
- `parameter` - Method parameters

### Implementation

#### Entry Point (CLIChannel.run)

```python
if args and args[0] == '--complete':
    self._handle_completion(args[1:])
    return
```

#### Completion Methods

```python
_handle_completion(completion_args)
    → _generate_completion_payload(shell, cursor, tokens)
        → _split_tokens(tokens) → (completed_tokens, current_fragment)
        → _suggest_for_context(completed_tokens, fragment)
            → Depth 0: _suggest_handlers(fragment)
            → Depth 1: _suggest_methods(handler, fragment)
            → Depth 1 (_system): _suggest_system_methods(fragment)
            → Depth 2+: _suggest_parameters(handler, method, fragment)
```

#### Handler Suggestions (Depth 0)

```python
def _suggest_handlers(self, fragment: str) -> List[dict]:
    """Suggest handler names from published_instances."""
    instances = self.publisher.published_instances

    for name, instance in instances.items():
        if fragment and not name.lower().startswith(fragment.lower()):
            continue

        yield {
            "type": "handler",
            "value": name,
            "display": name,
            "description": instance.__class__.__doc__ or "",
            "inline_hint": ""
        }
```

#### Method Suggestions (Depth 1)

```python
def _suggest_methods(self, handler_name: str, fragment: str) -> List[dict]:
    """Suggest methods for a handler using Router schema."""
    handler = self.publisher.published_instances[handler_name]

    # IMPORTANT: Use __class__.api to get blueprint schema
    schema = handler.__class__.api.describe()
    methods = schema.get('methods', {})

    for method_name, info in methods.items():
        if fragment and not method_name.lower().startswith(fragment.lower()):
            continue

        # Build inline hint from parameters
        params = info.get('parameters', [])
        inline_hint = " ".join(
            f"<{p['name']}>" if p.get('required') else f"[{p['name']}]"
            for p in params
        )

        yield {
            "type": "method",
            "value": method_name,
            "display": method_name,
            "description": info.get('description', ''),
            "inline_hint": inline_hint
        }
```

**Key**: Uses `handler.__class__.api.describe()` to get the class-level Router blueprint, not the instance-bound Router.

#### Parameter Suggestions (Depth 2+)

```python
def _suggest_parameters(self, handler_name: str, method_name: str, fragment: str):
    """Suggest parameters for a specific method."""
    handler = self.publisher.published_instances[handler_name]
    schema = handler.__class__.api.describe()
    method_schema = schema['methods'][method_name]

    for param in method_schema.get('parameters', []):
        if fragment and not param['name'].lower().startswith(fragment.lower()):
            continue

        yield {
            "type": "parameter",
            "value": param['name'],
            "display": param['name'],
            "description": param.get('description') or 'parameter',
            "inline_hint": f"<{param.get('type', 'any')}>",
            "required": param.get('required', False)
        }
```

### Shell Integration (Future)

The completion system is designed for integration with shell scripts:

**Bash** (`scripts/completion/bash.sh`):
```bash
_smpub_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local json=$(smpub --complete bash "$COMP_POINT" "${COMP_WORDS[@]:1}")
    # Parse JSON and populate COMPREPLY
}
complete -F _smpub_complete smpub
```

**Zsh** (`scripts/completion/zsh.sh`):
```zsh
_smpub_complete() {
    local json=$(smpub --complete zsh "$CURSOR" "${words[@]:1}")
    # Parse JSON and use compadd
}
compdef _smpub_complete smpub
```

**Fish** (`scripts/completion/fish.fish`):
```fish
complete -c smpub -a '(smpub --complete fish (commandline -cp) (commandline -opc)[2..])'
```

## Design Principles Summary

1. **Publisher is an app** (PublishedClass), not a special meta-object
2. **Publisher is the root app** (`.self` implicit)
3. **Thin facade pattern** (delegates to registries and channels)
4. **Self-managing objects** (each initializes, works, cleans up itself)
5. **Router-based dispatch** (SmartRoute handles all routing)
6. **Dynamic introspection** (completion uses `api.describe()`)
7. **Channel abstraction** (CLI, HTTP as transport layers)

## Component Relationships

```
Publisher (root PublishedClass)
├── registry (AppRegistry, RoutedClass)
│   ├── Router api with methods
│   └── manages: registration, loading, unloading
├── chan_registry (ChanRegistry, RoutedClass)
│   ├── Router api with methods
│   ├── channels: {cli: CLIChannel, http: HTTPChannel}
│   └── manages: channel discovery, instantiation
├── _system (SystemCommands, from PublishedClass)
│   └── introspection methods
└── applications: dict[str, PublishedClass]
    └── runtime cache of loaded apps

Channels (transport layer)
├── CLIChannel (cli_channel.py)
│   ├── run(args) - main entry point
│   ├── _handle_completion() - shell completion
│   └── _handle_business_command() - dispatch to handlers
└── HTTPChannel (http_channel.py)
    └── run(port, **kwargs) - FastAPI server (future)
```

## Testing the System

### Manual CLI Testing

```bash
# Basic command
smpub apps list

# Completion testing (bypass shell)
python -m smartpublisher.publisher --complete bash 0 ""
python -m smartpublisher.publisher --complete bash 0 "ap"
python -m smartpublisher.publisher --complete bash 0 "apps" ""
python -m smartpublisher.publisher --complete bash 0 "apps" "add" ""
```

### Expected Completion Results

| Command | Expected Output |
|---------|----------------|
| `--complete bash 0 ""` | Handlers: `_system`, `apps`, `chan` |
| `--complete bash 0 "ap"` | Partial match: `apps` |
| `--complete bash 0 "apps" ""` | Methods: `add`, `remove`, `list`, `getapp` |
| `--complete bash 0 "apps" "add" ""` | Params: `name`, `path`, `module`, `class_name` |

## Future Enhancements

### Completion System
- [ ] Shell installation scripts (`scripts/completion/`)
- [ ] `smpub install-completion <shell>` command
- [ ] Fuzzy matching support
- [ ] Caching for performance

### Publisher Features
- [ ] `start()`, `stop()`, `restart()` lifecycle methods
- [ ] Configuration file support
- [ ] Plugin system
- [ ] Event system for app/channel lifecycle
- [ ] Monitoring/metrics

### Channel Features
- [ ] HTTP channel with FastAPI
- [ ] WebSocket channel
- [ ] gRPC channel
- [ ] Message queue channels

All following the same principles:
- Delegate to specialized components
- Keep Publisher thin
- Maintain clean separation of concerns
- Use Router introspection for dynamic behavior

---

**Maintained by**: Genropy Team
**License**: MIT
**Part of**: Genro-Libs toolkit
