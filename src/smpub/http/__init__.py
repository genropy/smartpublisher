"""
HTTP/API module for smpub.

Provides FastAPI integration with automatic route generation
and OpenAPI documentation.
"""

from .fastapi_app import create_fastapi_app
from .openapi import generate_openapi_schema

__all__ = [
    "create_fastapi_app",
    "generate_openapi_schema",
]
