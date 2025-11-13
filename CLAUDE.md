# Claude Code Instructions - smpub

## Project Context

**smpub** (Smart Publisher) is a CLI/API framework based on SmartSwitch for building command-line and web applications with automatic dispatch.

### Current Status
- **Development Status**: Alpha (`Development Status :: 3 - Alpha`)
- **Version**: 0.1.0
- **Has Implementation**: Partial (core classes implemented, CLI/HTTP to be completed)
- **Dependencies**: smartswitch >= 0.1.0

### Project Overview

smpub provides:
- `Publisher` base class for applications
- `PublishedClass` mixin for handlers
- Registry system for app management (.published file)
- CLI entry point (`smpub` command)
- CLI/HTTP exposure control

## Repository Information

- **Owner**: genropy
- **Repository**: https://github.com/genropy/smartpublisher
- **Documentation**: https://smartpublisher.readthedocs.io (planned)
- **License**: MIT
- **Part of**: Genro-Libs toolkit

## Project Structure

```
smpub/
├── src/smpub/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # CLI entry point
│   ├── publisher.py         # Publisher class
│   └── published.py         # PublishedClass mixin
├── tests/                   # Tests (to be added)
├── docs/                    # Documentation (to be added)
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
2. **SmartSwitch integration**: Leverage smartswitch for dispatch
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

## Relationship with SmartSwitch

smpub **depends on** smartswitch:
- Uses `Switcher` for handler method dispatch
- Handlers define `api = Switcher(...)` class variable
- Publisher creates root `parent_api = Switcher()`
- Hierarchical API structure through parent linking

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
