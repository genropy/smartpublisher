# Claude Code Instructions - smartpublisher

## Project Context

**smartpublisher** (Smart Publisher) is a CLI/API framework based on SmartRoute for building command-line and web applications with automatic dispatch.

**Naming Convention**:
- **Package name**: `smartpublisher` (used in imports: `from smartpublisher import ...`)
- **CLI command**: `smpub` (kept short for user convenience)
- **Repository**: `genropy/smartpublisher`

### Current Status
- **Development Status**: Beta (`Development Status :: 4 - Beta`)
- **Version**: 0.3.0
- **Has Implementation**: Complete (all major features implemented)
- **Dependencies**: smartroute >= 0.11.0, smartasync >= 0.2.0

### Project Overview

smartpublisher provides:
- `Publisher` base class for applications
- `PublisherContext` for handler context management
- Registry system for app management
- CLI entry point (`smpub` command - note: command name is kept short)
- CLI/HTTP exposure control

## Repository Information

- **Owner**: genropy
- **Repository**: https://github.com/genropy/smartpublisher
- **Documentation**: https://smartpublisher.readthedocs.io (planned)
- **License**: MIT
- **Part of**: Genro-Libs toolkit

## Project Structure

```
smartpublisher/
├── src/smartpublisher/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # CLI entry point (smpub command)
│   ├── publisher.py         # Publisher class
│   ├── published.py         # PublisherContext and utilities
│   ├── http/                # HTTP server implementation
│   ├── interactive/         # Interactive CLI mode
│   └── validation/          # Pydantic validation
├── tests/                   # Test suite
├── docs/                    # Sphinx documentation
├── examples/                # Example applications
├── pyproject.toml          # Package configuration
├── README.md               # Project overview
├── LICENSE                 # MIT license
└── CLAUDE.md               # This file
```

## Language Policy

- **Code, comments, and commit messages**: English
- **Documentation**: English (primary)
- **Communication with user**: Italian (per user preference)

## Git Commit Policy

- **NEVER** include Claude as co-author in commits
- **ALWAYS** remove "Co-Authored-By: Claude <noreply@anthropic.com>" line
- Use conventional commit messages following project style

## Development Guidelines

### Core Principles

1. **Clean separation**: Publisher (orchestration) vs PublishedClass (handlers)
2. **SmartRoute integration**: Leverage smartroute for dispatch
3. **Flexible exposure**: cli/openapi flags per handler
4. **Registry system**: Local (.published) and global (~/.smartlibs/publisher/)

### Testing

Tests to be implemented:
- Publisher initialization
- publish() method
- parent_api injection
- CLI registry operations
- App loading and execution

### Current TODOs

1. **CLI Mode Implementation** (`_run_cli()` in publisher.py)
   - Parse commands
   - Dispatch to handlers
   - Generate help from docstrings/signatures

2. **HTTP Mode Implementation** (`_run_http()` in publisher.py)
   - FastAPI integration
   - Auto-generate routes from handlers
   - OpenAPI spec generation

3. **Tests**
   - Unit tests for all classes
   - Integration tests for CLI
   - Registry management tests

4. **Documentation**
   - API reference
   - User guide
   - Examples

## Known Design Decisions

1. **PublishedClass with __slots__**: Uses slots for `parent_api` to allow subclasses with __slots__
2. **Registry files**: JSON format for simplicity and human readability
3. **Convention over configuration**: Apps expected to have `main.py` with `MainClass`
4. **Auto-detect mode**: CLI if args present, HTTP otherwise

## Relationship with SmartRoute

smartpublisher **depends on** smartroute:
- Uses `Router` for handler method dispatch
- Handlers define `api = Router(...)` class variable
- Publisher creates root `Router()` for routing
- Hierarchical API structure through composition
- SmartRoute provides the dispatch mechanism, smartpublisher adds CLI/HTTP interfaces

## Development Workflow

**MANDATORY sequence before every push:**

1. **Run pytest locally**
   ```bash
   pytest
   ```

2. **Run ruff locally**
   ```bash
   ruff check .
   ```

3. **Push only if both pass**
   ```bash
   git push origin main
   ```
   Pre-push hook will automatically run ACT for final validation.

**CRITICAL RULES:**
- ❌ **NEVER use `--no-verify`** without explicit user authorization
- ✅ **ALWAYS investigate** pre-push failures instead of bypassing
- ✅ Local testing is FAST (seconds) vs ACT is SLOW (minutes)
- ✅ "LOCALE PRIMA, ACT POI" (Local first, ACT after)

**Rationale**: Local tests catch errors immediately. ACT is the final safety net, not the first line of defense.

## Mistakes to Avoid

❌ **DON'T**:
- Add implementation code to CLI that should be in Publisher
- Break backward compatibility without major version bump
- Skip tests when adding features
- Include Claude as co-author in commits
- Use `--no-verify` to bypass pre-push hook without authorization

✅ **DO**:
- Keep CLI focused on registry management and app loading
- Keep Publisher focused on orchestration
- Maintain clean separation of concerns
- Test all public APIs
- Run pytest and ruff locally before pushing

## Quick Reference

| File | Purpose |
|------|---------|
| cli.py | Entry point, registry management, app loading |
| publisher.py | Base class for applications |
| published.py | Mixin for handlers |
| __init__.py | Package exports |

---

**Author**: Genropy Team
**License**: MIT
**Python**: 3.10+
**Part of**: Genro-Libs toolkit
