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

For gum-based interactive parameter prompting:

```bash
pip install smpub[gum]
```

**Note**: This also requires the `gum` CLI tool:

```bash
# macOS
brew install gum

# Linux
curl https://raw.githubusercontent.com/charmbracelet/gum/main/install.sh | bash

# Windows
scoop install gum
```

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
