# SmartPublisher - Architecture Documentation

## Overview

SmartPublisher è un framework per costruire applicazioni CLI/API usando SmartSwitch come sistema di dispatch.

**Principi chiave**:
- Separazione netta tra orchestrazione (Publisher) e business logic (PublishedClass)
- Zero print statements nella business logic (solo dati strutturati)
- SmartSwitch come unica fonte di verità (no inspect, no custom validation)
- Multi-channel: stessa business logic su CLI, HTTP, WebSocket, ecc.

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Publisher                            │
│  (ONE instance - coordina tutto il sistema)                 │
│                                                              │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │  AppRegistry │  │        Channels                     │  │
│  │              │  │  ┌──────────┐  ┌──────────┐        │  │
│  │ .apps add    │  │  │ CLI      │  │ HTTP     │  ...   │  │
│  │ .apps list   │  │  └──────────┘  └──────────┘        │  │
│  │ .apps remove │  │                                     │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Loaded Apps (cache)                        │  │
│  │  myapp → MyApp instance (inherits PublishedClass)    │  │
│  │  shop  → ShopApp instance                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    PublishedClass (Mixin)                    │
│  (User apps inherit - ogni app ha il SUO Switcher tree)     │
│                                                              │
│  MyApp (inherits PublishedClass)                            │
│  ├─ api: Switcher(name="root")  ← Root della app           │
│  ├─ published_instances: {                                  │
│  │    "shop": ShopHandler,                                  │
│  │    "users": UsersHandler,                                │
│  │    "_system": SystemCommands                             │
│  │  }                                                       │
│  └─ _publisher: riferimento al Publisher                    │
│                                                              │
│  def on_init(self):                                         │
│      self.publish("shop", ShopHandler())                    │
│      self.publish("users", UsersHandler())                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Classes

### 1. **Publisher** (ONE instance per sistema)

**File**: `publisher.py`

**Responsabilità**:
- Gestisce il registry (AppRegistry)
- Gestisce i channels (CLI, HTTP, ecc.)
- Carica/scarica apps
- Coordina il routing tra apps e channels

**NON contiene**:
- Business logic delle app
- Transport code (quello sta nei channels)

**Esempio**:
```python
publisher = Publisher()
app = publisher.load_app("myapp")  # Carica dal registry
publisher.run_cli()  # Avvia CLI channel
publisher.run_http(port=8000)  # Avvia HTTP server
```

---

### 2. **PublishedClass** (Mixin per user apps)

**File**: `published.py`

**Responsabilità**:
- Base class per apps degli utenti
- Fornisce root Switcher per l'app
- Metodo `publish()` per registrare handlers
- System commands automatici (_system)
- Lifecycle hooks (on_add, on_remove)

**Caratteristiche**:
- Ogni app ha il SUO Switcher tree (isolato)
- Riferimento a Publisher via `_publisher`
- Comunica col Publisher tramite metodi del mixin

**Esempio**:
```python
class MyApp(PublishedClass):
    def on_init(self):
        # Pubblica handlers
        self.publish("shop", ShopHandler())
        self.publish("users", UsersHandler())

    def smpub_on_add(self):
        # Hook quando registrata
        return {"message": "MyApp ready!"}
```

---

### 3. **AppRegistry** (Handler con Switcher)

**File**: `registry.py`

**Responsabilità**:
- Gestione apps registrate (JSON-based)
- Comandi: `add`, `remove`, `list`, `getapp`
- Discovery (local + global registry)
- Caricamento dinamico delle apps

**Caratteristiche**:
- Ha il suo Switcher: `api = Switcher(name="apps")`
- Comandi esposti via `@api` decorator
- Accessibile da CLI: `smpub .apps <command>`

**Registry locations**:
- Local: `.published` (directory corrente)
- Global: `~/.smartlibs/publisher/registry.json`

---

### 4. **Channels** (Transport layers)

**Files**: `channels/cli.py`, `channels/http.py`

**Responsabilità**:
- Esporre business logic su specifici transport
- Ogni channel ha il SUO Switcher per utility commands
- NO business logic (quella sta nelle apps)

**Struttura**:
```python
class PublisherCLI:
    cli_api = Switcher(name="cli")  # CLI-specific utilities

    def __init__(self, publisher):
        self.publisher = publisher

    @cli_api
    def help(self) -> dict:
        """CLI-specific help command"""

    def run(self, args):
        """Route commands usando SmartSwitch"""
```

**Due livelli di comandi**:
1. **Business commands**: Da `app.api` (channel-agnostic)
   - `myapp shop list`
   - `myapp users create`

2. **Channel commands**: Da `channel.xxx_api` (transport-specific)
   - CLI: `help`, `version`
   - HTTP: `health`, `openapi_schema`, `metrics`

---

## CLI Routing Convention

### Dot Prefix Convention

**Sistema commands** iniziano con `.` (dot):
```bash
smpub .apps add myapp /path      # Registry command
smpub .apps list                 # Lista apps
smpub .apps remove myapp         # Rimuovi app
```

**App commands** NON hanno il dot:
```bash
smpub myapp shop list            # App command (shorthand)
smpub myapp _system list_handlers
```

### Routing Logic

```python
first_arg = sys.argv[1]

if first_arg.startswith('.'):
    # Sistema command
    system_handler = first_arg[1:]  # Remove dot → "apps"
    # Route to system handler
else:
    # App command (shorthand)
    # Equivalente a: .apps getapp <app_name>
    app_name = first_arg
    app = publisher.load_app(app_name)
    # Route to app
```

---

## Bash Completion

**Principio**: SmartSwitch è la fonte di verità anche per completion!

### Come Funziona

1. Bash completion script chiama: `smpub --complete <level> <args...>`
2. CLI restituisce lista di suggerimenti da `Switcher.describe()`
3. Bash usa la lista per tab completion

### Livelli

**Level 0** (dopo `smpub`):
```python
suggestions = ['.apps'] + registry.list_app_names()
# → .apps myapp otherapp
```

**Level 1** (dopo `smpub .apps`):
```python
schema = AppRegistry.api.describe()
suggestions = schema['methods'].keys()
# → add list remove getapp
```

**Level 1** (dopo `smpub myapp`):
```python
app = load_app("myapp")
suggestions = app.published_instances.keys()
# → shop users _system
```

**Level 2** (dopo `smpub myapp shop`):
```python
handler = app.published_instances['shop']
schema = handler.__class__.api.describe()
suggestions = schema['methods'].keys()
# → list create update delete
```

---

## Data Flow

### 1. App Registration

```
User: smpub .apps add myapp /path/to/app

┌─────────────────────────────────────┐
│ CLI (cli.py)                        │
│ ├─ Parse: .apps add myapp /path    │
│ ├─ Route to system handler: "apps" │
│ └─ Get registry (local/global)     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ AppRegistry (registry.py)           │
│ ├─ Call: registry.api.get("add")   │
│ ├─ Execute: add(myapp, /path)      │
│ ├─ Save to JSON                     │
│ └─ Return: {"status": "registered"}│
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ OutputFormatter (cli.py)            │
│ └─ Format dict → CLI output         │
└─────────────────────────────────────┘
              ↓
Output: ✓ App 'myapp' registered
```

### 2. App Command Execution

```
User: smpub myapp shop list

┌─────────────────────────────────────┐
│ CLI (cli.py)                        │
│ ├─ Parse: myapp shop list          │
│ ├─ Discover app in registry        │
│ └─ Load app (PublishedClass)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Publisher (publisher.py)            │
│ ├─ Check cache                      │
│ ├─ Load from registry if needed     │
│ ├─ Call app.smpub_on_add()         │
│ └─ Return PublishedClass instance   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ PublisherCLI (channels/cli.py)      │
│ ├─ Parse: shop list                │
│ ├─ Access: app.api['shop']['list'] │
│ ├─ Call via SmartSwitch             │
│ └─ Get structured data              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ ShopHandler (user code)             │
│ ├─ Business logic                   │
│ ├─ Return dict (NO print!)         │
│ └─ SmartSwitch validates            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ OutputFormatter (cli.py)            │
│ └─ Format dict → CLI output         │
└─────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. NO Print in Business Logic

**Problema**: Print statements rendono il codice non riusabile su canali diversi

**Soluzione**:
- Business logic restituisce dict
- Formattazione solo al bordo (OutputFormatter nei channels)

**Esempio**:
```python
# ❌ BAD
def list_products(self):
    print("Products:")
    for p in self.products:
        print(f"  - {p['name']}: ${p['price']}")

# ✅ GOOD
def list(self) -> dict:
    return {
        "total": len(self.products),
        "products": self.products
    }
```

### 2. SmartSwitch come Fonte di Verità

**Problema**: Duplicazione di introspection logic (help, validation, completion)

**Soluzione**: Usare SOLO `Switcher.describe()`
- Help → `switcher.describe()`
- Completion → `switcher.describe()['methods'].keys()`
- Validation → SmartSwitch automatico
- OpenAPI → generato da `switcher.describe()`

**Vietato**:
- ❌ `inspect` module
- ❌ Custom Pydantic validation
- ❌ Manual argument parsing

### 3. Separazione Publisher/PublishedClass

**Perché due classi?**

- **Publisher**: Sistema centrale, ONE instance
  - Orchestrazione
  - Registry
  - Channels

- **PublishedClass**: Mixin per user apps, MANY instances
  - Business logic
  - Root Switcher della app
  - Handlers

**Vantaggio**: Separazione chiara di responsabilità

### 4. Dot Prefix per Sistema Commands

**Perché `.apps` e non `apps`?**

- ✅ Nessun conflitto con nomi di app
- ✅ Distinzione visiva chiara
- ✅ Coerenza con convenzione Unix (file nascosti)
- ✅ Espandibile (`.config`, `.version`, ecc.)

---

## File Organization

```
src_new/
├── ARCHITECTURE.md           # Questo file
├── __init__.py               # Exports
│
├── publisher.py              # Publisher class (coordinatore)
├── published.py              # PublishedClass mixin
├── registry.py               # AppRegistry handler
│
├── cli.py                    # CLI entry point (smpub)
├── output_formatter.py       # OutputFormatter
├── system_commands.py        # SystemCommands handler
│
├── channels/
│   ├── __init__.py
│   ├── cli.py                # PublisherCLI channel
│   └── http.py               # PublisherHTTP channel
│
├── bash_completion/
│   ├── smpub                 # Bash completion script
│   └── README.md             # Installation guide
│
└── example_app.py            # Example app (inherits PublishedClass)
```

---

## Usage Examples

### Creating an App

```python
from smartswitch import Switcher
from smartpublisher import PublishedClass

# Handler with business logic
class ShopHandler:
    api = Switcher(name="shop")

    @api
    def list(self) -> dict:
        return {"products": [...]}

    @api
    def create(self, name: str, price: float) -> dict:
        return {"status": "created", "name": name}

# App (inherits PublishedClass)
class ShopApp(PublishedClass):
    def on_init(self):
        self.publish("shop", ShopHandler())
```

### Registering and Using

```bash
# Register app
smpub .apps add myshop /path/to/app main ShopApp

# List apps
smpub .apps list

# Use app (CLI)
smpub myshop shop list
smpub myshop shop create --name "Laptop" --price 999.99

# Start HTTP server
smpub serve myshop --port 8000
```

### HTTP Access

```bash
# Business endpoints
curl http://localhost:8000/shop/list
curl -X POST http://localhost:8000/shop/create \
  -d '{"name": "Laptop", "price": 999.99}'

# HTTP utility endpoints
curl http://localhost:8000/_http/health
curl http://localhost:8000/_http/openapi
```

---

## Important Notes

1. **Publisher è singleton-like**: Usa `get_publisher()` per accedere all'istanza default
2. **Apps sono isolate**: Ogni app ha il suo Switcher tree separato
3. **Registry è JSON**: Facile da editare manualmente se necessario
4. **Channels sono pluggable**: Aggiungi custom channels con `publisher.add_channel()`
5. **SmartSwitch è la fonte di verità**: Non duplicare introspection logic!

---

**Last Updated**: 2025-11-16
**Version**: 0.3.0 (architecture refactor with Publisher/PublishedClass)
