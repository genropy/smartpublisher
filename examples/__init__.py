"""
Examples for smpub.

This package contains example applications demonstrating smpub usage.

## Current Examples

### sample_shop/ - Complete E-commerce Example
Standalone Python library with SQLite backend. Demonstrates:
- Pure Python usage (no smpub required)
- smartswitch plugin benefits (Pydantic validation, etc.)
- Clean separation of concerns
- Comprehensive tests (10/10 passing)
- Interactive Jupyter notebook
- Complete documentation

**Start here!** This is the primary example.

### published_shop/ - Publisher Example
Shows how to optionally publish sample_shop for CLI/HTTP access.
Demonstrates that smpub is a thin publishing layer.

## Old Examples

See `old_examples/` for archived examples that may be incomplete or use old patterns.
"""

__all__ = ["sample_shop", "published_shop"]
