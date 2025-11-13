# smpub Documentation Revision - Focus Areas

## Current State

- Basic API documentation exists
- Need to emphasize **app registration and usage workflow**
- Need clear separation between framework docs and demo docs

## Key Changes Needed

### 1. App Registry System - Make It Central

The registry system is a **key feature** but currently underemphasized. Users need to understand:

**Registration Flow**:
```
1. Write your app → 2. Register it → 3. Use it anywhere
```

**Registry Commands** (to document prominently):
```bash
# Register an app
smpub register myapp /path/to/myapp

# List registered apps
smpub list

# Show app info
smpub info myapp

# Run registered app (CLI mode)
smpub run myapp command args

# Run registered app (HTTP mode)
smpub serve myapp --port 8000

# Unregister app
smpub unregister myapp
```

### 2. Documentation Structure

```
docs/
├── index.md                    # Overview + Quick Start
├── user-guide/
│   ├── installation.md
│   ├── quickstart.md
│   ├── publishing-guide.md     # How to publish your library
│   └── registry.md            # ⭐ NEW: Registry system in depth
│
├── guide/
│   ├── publisher.md           # Writing Publishers
│   ├── handlers.md            # Writing handlers with Switcher
│   ├── cli-mode.md            # Using CLI
│   ├── http-mode.md           # Using HTTP API
│   ├── validation.md          # Pydantic validation
│   ├── interactive.md         # Interactive prompts
│   └── best-practices.md
│
├── examples/
│   ├── index.md               # Examples overview
│   ├── calculator.md          # Simple example
│   └── demo-shop.md          # ⭐ Link to separate demo_shop docs
│
├── api/
│   ├── publisher.md
│   ├── published.md
│   ├── registry.md            # ⭐ NEW: Registry API reference
│   ├── http.md
│   ├── interactive.md
│   └── validation.md
│
└── appendix/
    ├── architecture.md
    ├── smartswitch.md
    └── philosophy/
        └── why-smpub.md
```

### 3. Key Messages to Emphasize

#### Message 1: "Built with SmartSwitch? Publishing is trivial"
Show that if you use SmartSwitch for your library, adding smpub is just:
```python
from smartpublisher import Publisher
from mylib import MyClass

class MyApp(Publisher):
    def on_init(self):
        self.publish("myservice", MyClass())

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

#### Message 2: "Register once, use everywhere"
```bash
# Register
smpub register myapp /path/to/myapp

# Now use from anywhere
smpub run myapp command
smpub serve myapp
```

#### Message 3: "CLI + HTTP for free"
Same code gives you both:
- CLI: `python main.py myservice command args`
- HTTP: `curl http://localhost:8000/myservice/command`
- Swagger: `http://localhost:8000/docs`

### 4. Quick Start Should Show Registry

Current quick start probably shows inline usage. Should show:

```markdown
## Quick Start

1. Install smpub
2. Write a simple Publisher (5 lines)
3. Register it: `smpub register myapp .`
4. Use it: `smpub run myapp command`
5. Or serve it: `smpub serve myapp`
```

### 5. Examples Organization

- **Simple examples** in smpub docs (calculator, hello world)
- **Complex demos** in separate docs (demo_shop, future demos)
- Link to demos with: "For a complete example, see [Demo Shop](https://smpub-demo-shop.readthedocs.io)"

## Action Items

- [ ] Create `docs/user-guide/registry.md` - Comprehensive registry guide
- [ ] Create `docs/api/registry.md` - Registry API reference
- [ ] Update `docs/index.md` - Make registry prominent in quick start
- [ ] Update `docs/guide/cli-mode.md` - Show registered app usage
- [ ] Update `docs/examples/index.md` - Link to demo_shop separate docs
- [ ] Create `docs/examples/demo-shop.md` - Bridge page with link

## Demo Shop Documentation

Demo Shop will have **separate ReadTheDocs project**:
- URL: `smpub-demo-shop.readthedocs.io`
- Config: `.readthedocs-demo.yaml`
- Focus: Document sample_shop library (no smpub references)
- Bridge: Small page in smpub docs linking to it

## Philosophy

**smpub docs**: Framework features, registry, publishing pattern
**demo docs**: Real-world applications, architecture, deep dives

This keeps smpub docs focused and prevents it from appearing overwhelming.

---

**Status**: Planning phase
**Next**: Complete demo_shop structure, then revise smpub docs
