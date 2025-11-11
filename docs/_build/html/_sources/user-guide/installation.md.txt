# Installation

## Requirements

- Python 3.10 or higher
- pip package manager

## Basic Installation

Install smpub from PyPI:

```bash
pip install smpub
```

This installs the core package with CLI and basic functionality.

## Optional Dependencies

### HTTP/API Support

For FastAPI integration and Swagger UI:

```bash
pip install smpub[http]
```

This includes:
- FastAPI
- uvicorn with standard extensions

### Interactive Mode

For interactive parameter prompting with questionary:

```bash
pip install questionary
```

Questionary is a pure Python package that works on all platforms (Windows, macOS, Linux).

### Development Tools

For contributing to smpub:

```bash
pip install smpub[dev]
```

This includes pytest, coverage, black, ruff, and mypy.

### Documentation

For building documentation:

```bash
pip install smpub[docs]
```

This includes mkdocs, mkdocs-material, and mkdocstrings.

### All Dependencies

Install everything:

```bash
pip install smpub[all]
```

## Verify Installation

Check that smpub is installed correctly:

```bash
smpub --version
python -c "import smpub; print(smpub.__version__)"
```

## Next Steps

- [Quick Start](quickstart.md) - Get started with smpub
- [Publishing Guide](publishing-guide.md) - Learn how to expose your library
