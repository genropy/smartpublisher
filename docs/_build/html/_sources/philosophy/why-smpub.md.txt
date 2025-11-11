# Why smpub? The Missing Link Between CLI and API

> **TL;DR**: smpub lets you write your business logic once with SmartSwitch, then instantly expose it as both CLI commands and REST APIs. No boilerplate, no duplication, no choosing between "tool for ops" or "service for developers." This is the second article in our series on building consistent developer toolkits.

---

You've just written a beautiful data processing function. Clean, tested, typed. Now someone asks: "Can we call this from the command line?"

Sure, you add Click decorators.

Then: "Can we expose this as an API for the web service?"

Now you're writing FastAPI routes that look suspiciously like your Click commands.

Then: "Can we add the third one too?"

**Stop. There's a better way.**

## Previously, on SmartSwitch...

In our previous article on SmartSwitch (see [SmartSwitch documentation](https://github.com/genropy/smartswitch)), we explored SmartSwitch as a standard dispatch pattern for your toolkit. We established that:

- **SmartSwitch organizes functions** with decorator-based registration
- **Three dispatch modes**: by-name, by-type (typerule), by-value (valrule)
- **It's a foundation**, not just dispatch - consistent patterns enable powerful tools

But we left something hanging: *"What tools can understand and extend SmartSwitch handlers?"*

**Enter smpub**: The framework that turns SmartSwitch handlers into production interfaces with zero additional code.

## The Write-Once Problem

Every internal tool faces the same question: **How will it be used?**

**Developers want**:
- HTTP API for automation
- JSON responses for parsing
- OpenAPI docs for integration

**Ops teams want**:
- CLI for scripting
- Direct execution without servers
- Interactive prompts for complex parameters

**You want**:
- To write the logic ONCE
- Not maintain two interfaces
- Not duplicate validation, docs, and type checking

**Traditional approach**: Pick one, promise to add the other later (spoiler: you never do).

## The smpub Pattern: SmartSwitch + Publishing

Building on SmartSwitch's foundation, smpub adds one key concept: **publishing**.

### Step 1: Define Handlers with SmartSwitch

```python
from smartswitch import Switcher

handlers = Switcher()

@handlers
def process_data(input_file: str, output_format: str = "json") -> dict:
    """Process data from input file.

    Args:
        input_file: Path to input file
        output_format: Output format (json, csv, xml)

    Returns:
        Processed data dictionary
    """
    # Your business logic here
    data = load_file(input_file)
    return transform(data, output_format)

@handlers
def analyze_results(data_dir: str, threshold: float = 0.5) -> list:
    """Analyze results from directory.

    Args:
        data_dir: Directory containing data files
        threshold: Analysis threshold (0.0-1.0)

    Returns:
        List of analysis results
    """
    # Your analysis logic
    return perform_analysis(data_dir, threshold)
```

**This is just SmartSwitch**. Clean handlers, no framework noise, fully testable.

### Step 2: Publish with smpub

```python
from smpub import Publisher, PublishedClass
from smpub.apiswitcher import ApiSwitcher

class DataTools(PublishedClass):
    api = ApiSwitcher(prefix='data_')

    @api
    def process_data(self, input_file: str, output_format: str = "json") -> dict:
        """Process data from input file."""
        data = load_file(input_file)
        return transform(data, output_format)

    @api
    def analyze_results(self, data_dir: str, threshold: float = 0.5) -> list:
        """Analyze results from directory."""
        return perform_analysis(data_dir, threshold)

class MyApp(Publisher):
    def initialize(self):
        self.publish(DataTools(), cli=True, openapi=True)

app = MyApp()
```

**That's it.** Same methods, now published.

### Step 3: Register and Use

```bash
# Register your app with smpub
smpub add myapp /path/to/main.py

# Use via CLI
smpub myapp data process-data --input-file data.csv --output-format json

# Interactive mode with TUI
smpub myapp data process-data --interactive

# Start HTTP server
smpub myapp serve

# Or specify port
smpub myapp serve 8080
```

**Now available via HTTP**:
```bash
# Your handlers are REST endpoints
curl -X POST http://localhost:8080/data/process_data \
  -H "Content-Type: application/json" \
  -d '{"input_file": "data.csv", "output_format": "json"}'

# OpenAPI docs automatically generated
open http://localhost:8080/docs
```

## What You Actually Get

### 1. **Zero Boilerplate Interfaces**

**Without smpub**:
```python
# cli.py - 50 lines of Click decorators
import click

@click.command()
@click.option('--input-file', required=True)
@click.option('--output-format', default='json')
def process_data(input_file, output_format):
    # Call actual function
    result = core.process_data(input_file, output_format)
    print(json.dumps(result))

# api.py - 50 lines of FastAPI routes
from fastapi import FastAPI
from pydantic import BaseModel

class ProcessRequest(BaseModel):
    input_file: str
    output_format: str = "json"

@app.post("/process_data")
def process_data(req: ProcessRequest):
    # Call actual function
    return core.process_data(req.input_file, req.output_format)
```

**With smpub**:
```python
# ONE method definition
@api
def process_data(self, input_file: str, output_format: str = "json") -> dict:
    """Process data from input file."""
    # Your actual logic
    return transform(load_file(input_file), output_format)
```

CLI, HTTP, and OpenAPI docs generated automatically.

### 2. **Registry Management**

```bash
# Register app
smpub add myapp /path/to/main.py

# List registered apps
smpub list

# Remove app
smpub remove myapp

# Show app details
smpub show myapp
```

Your tools become **discoverable**. No more "where did I put that script?"

### 3. **Interactive Mode**

```bash
# Launch TUI form
smpub myapp data process-data --interactive
```

Gets you:
- Type-aware input fields (text, numbers, booleans)
- Real-time validation
- Default values pre-filled
- Rich terminal UI via Textual

Perfect for:
- Complex parameters
- Long text inputs
- Teaching new users

### 4. **Hierarchical Commands**

SmartSwitch's hierarchical dispatch becomes hierarchical CLI:

```python
class UserTools(PublishedClass):
    api = ApiSwitcher(prefix='user_')

    @api
    def create(self, name: str, email: str) -> str:
        """Create user."""
        pass

    @api
    def delete(self, user_id: int) -> str:
        """Delete user."""
        pass

class AdminTools(PublishedClass):
    api = ApiSwitcher(prefix='admin_')

    @api
    def promote(self, user_id: int) -> str:
        """Promote to admin."""
        pass
```

Becomes:
```bash
smpub myapp user create --name Alice --email alice@example.com
smpub myapp user delete --user-id 123
smpub myapp admin promote --user-id 123
```

And:
```
POST /user/create
POST /user/delete
POST /admin/promote
```

### 5. **Type Validation Everywhere**

```python
@api
def analyze(self, threshold: float = 0.5, max_items: int = 100) -> list:
    """Analyze with validation."""
    pass
```

Pydantic validates:
- **CLI**: `--threshold abc` → error
- **HTTP**: `{"threshold": "abc"}` → 422 validation error
- **Interactive**: Form won't accept invalid input

One definition, validation everywhere.

## The Registry Pattern

smpub maintains a registry of your published apps:

**Local registry**: `.published` file in your project
```json
{
  "app_name": "myapp",
  "main_file": "main.py",
  "handlers": ["DataTools", "UserTools"]
}
```

**Global registry**: `~/.smartlibs/publisher/apps.json`
```json
{
  "myapp": {
    "path": "/path/to/project",
    "registered": "2025-11-10T10:30:00"
  }
}
```

**Benefits**:
- Apps discoverable system-wide
- Version control tracks `.published` (team shares app definitions)
- Global registry is personal (each dev can have different paths)

## What smpub Is NOT

Let's be clear about boundaries (these are **design choices**, not limitations):

### ❌ Not a Web Framework
- No HTML templates, sessions, or cookies
- **Use instead**: FastAPI + Jinja2, Flask, Django
- **You CAN**: Connect a frontend to smpub's HTTP API

### ❌ Not a CLI Customization Framework
- Standard `--arg value` syntax only
- No custom parsers, ranges, or choices
- **Use instead**: Click/Typer for maximum CLI control
- **Why**: Custom parsers break automatic API generation

### ❌ Not for Public APIs
- Built for internal tools, not public-facing services
- No rate limiting, API keys, or complex auth (yet)
- **Use instead**: FastAPI directly for public APIs
- **You CAN**: Add auth via FastAPI middleware (it's just FastAPI under the hood)

## When to Use smpub

### ✅ Perfect Fit

**Internal tools with dual needs**:
- Database admin tools (CLI for ops, API for automation)
- Deployment scripts (run locally or trigger via webhook)
- Data pipelines (CLI for dev, API for production)
- DevOps utilities (CLI for manual ops, API for CI/CD)

**You're writing multiple tools**:
- Not a one-off script
- Building a suite of internal utilities
- Want consistent patterns across tools

**You value speed over customization**:
- Rapid prototyping
- Internal tooling where "good enough" beats "perfect"
- Teams that prefer convention over configuration

### ❌ Wrong Fit

**Your tool is too simple**:
```python
# Don't use smpub for this
@app.command()
def hello(name: str):
    print(f"Hello {name}")
```
Just use Click. Adding smpub is overkill.

**You need complex CLI**:
```python
# smpub can't do this
@click.option('--range', type=click.IntRange(1, 100))
@click.option('--choice', type=click.Choice(['a', 'b', 'c']))
def complex_command(range, choice):
    pass
```
Use Click/Typer directly.

**You're building a public API**:
- Need custom auth, rate limiting, complex middleware
- Use FastAPI directly, smpub adds no value

**You only need CLI OR API**:
- Only CLI? → Use Click/Typer (simpler)
- Only API? → Use FastAPI (more flexible)
- Need both? → **Use smpub**

## The Architectural Win: ApiSwitcher

One detail worth noting: **ApiSwitcher creates Pydantic models at decoration time**, not runtime.

**Why this matters**:

FastAPI generates OpenAPI schemas at app startup by introspecting type hints. If you create Pydantic models dynamically at runtime, FastAPI can't see them.

**smpub's solution**:

```python
class ApiSwitcher(Switcher):
    def __call__(self, func):
        """Decorate and create model NOW."""
        decorated = super().__call__(func)
        # Create Pydantic model at decoration time
        model = self._create_pydantic_model(func)
        self._pydantic_models[func.__name__] = model
        return decorated
```

Models exist when FastAPI inspects the app → OpenAPI docs work correctly.

Not revolutionary, but **correct** and **non-obvious** if you're building FastAPI integrations.

## Real-World Workflow

### Development

```bash
# Write handlers
vim main.py

# Test directly
python main.py data process-data --input-file test.csv

# Or register and use via smpub
smpub add myapp .
smpub myapp data process-data --input-file test.csv
```

### Local Testing

```bash
# Start server
smpub myapp serve 8000

# Test HTTP endpoint
curl -X POST http://localhost:8000/data/process_data \
  -d '{"input_file": "test.csv", "output_format": "json"}'

# Check OpenAPI docs
open http://localhost:8000/docs
```

### Production Deployment

```bash
# Deploy as service
smpub myapp serve 8080

# Or use gunicorn/uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080

# Ops can still use CLI
smpub myapp data process-data --input-file /data/production.csv
```

### Team Sharing

```bash
# Commit .published to git
git add .published
git commit -m "Add smpub app definition"

# Teammates register locally
git pull
smpub add myapp .
smpub list  # myapp now available
```

## Comparison: The Full Picture

| Feature | Click/Typer | FastAPI | smpub | FastAPI + Typer |
|---------|-------------|---------|-------|-----------------|
| CLI interface | ✅ | ❌ | ✅ | ✅ |
| HTTP API | ❌ | ✅ | ✅ | ✅ |
| OpenAPI docs | ❌ | ✅ | ✅ | ✅ |
| Interactive TUI | ❌ | ❌ | ✅ | ❌ |
| Single definition | ✅ | ✅ | ✅ | ❌ (two wrappers) |
| Registry management | ❌ | ❌ | ✅ | ❌ |
| Custom CLI | ✅ Full | ❌ | ⚠️ Standard | ✅ Full |
| Custom HTTP | ❌ | ✅ Full | ⚠️ Standard | ✅ Full |
| Boilerplate | Low | Low | **Minimal** | **High** |

**The trade-off**: smpub gives you less control but eliminates duplication.

## Key Takeaways

If you remember nothing else:

**1. SmartSwitch + Publishing = Dual Interfaces**
- Write handlers with SmartSwitch pattern
- Publish with smpub → Get CLI + HTTP
- Same validation, docs, and logic everywhere

**2. Registry Makes Tools Discoverable**
- `smpub add myapp .` - register once
- `smpub list` - see all tools
- `smpub myapp handler method` - use anywhere

**3. It's Just FastAPI**
- Full FastAPI app accessible
- Add middleware, auth, custom routes
- smpub doesn't lock you in

**4. Convention Over Configuration**
- Standard `--arg value` CLI syntax
- REST POST endpoints
- Pydantic validation
- Accept constraints, gain speed

**5. The Real Question**
- Not "Is this the best framework?"
- But "Am I writing multiple internal tools that need dual exposure?"
- If yes → smpub saves massive time
- If no → stick with Click or FastAPI alone

---

## What's Next?

This completes our two-part series on building consistent developer toolkits:

**Part 1**: [Why SmartSwitch?](https://github.com/genropy/smartswitch) - Standard dispatch patterns
**Part 2**: Why smpub? (this article) - Dual CLI/API interfaces

**The pattern works**:
1. Adopt SmartSwitch as your dispatch standard
2. Use smpub to expose SmartSwitch handlers
3. Write once, deploy everywhere

---

**Project**: smpub
**Version**: 0.1.0 (Alpha)
**Python**: 3.10+
**License**: MIT
**Dependencies**: smartswitch, fastapi, textual (optional)
**GitHub**: [github.com/genropy/smpub](https://github.com/genropy/smpub)

**Use it for internal tools. Don't use it for public APIs.**

**But if you're building a suite of internal utilities, smpub eliminates an entire category of boilerplate.**

---

*Found this helpful? Questions? Leave a comment below. Want to see smpub in action? Check out the [examples](../examples/index.md) for complete working demos.*
