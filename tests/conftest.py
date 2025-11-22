from __future__ import annotations

"""Pytest fixtures for smartpublisher tests."""

import itertools
import uuid
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import pytest
from smartpublisher.publisher import Publisher


@dataclass
class AppSpec:
    target: str
    file_path: Path
    module: str
    class_name: str


@pytest.fixture
def create_app(tmp_path: Path):
    """Factory fixture that builds a temporary application module."""
    counter = itertools.count()

    def _create_app(module: str | None = None, class_name: str = "Main") -> AppSpec:
        idx = next(counter)
        module_name = module or f"app_module_{idx}_{uuid.uuid4().hex}"
        app_dir = tmp_path / f"app_{idx}"
        app_dir.mkdir()
        module_path = app_dir / f"{module_name}.py"
        module_path.write_text(
            dedent(
                f"""
                from smartroute import Router, RoutedClass, route


                class {class_name}(RoutedClass):
                    def __init__(self, *args, **kwargs):
                        super().__init__()
                        self.args = args
                        self.kwargs = kwargs
                        self.api = Router(self, name="app").plug("pydantic")

                    @route("api")
                    def ping(self):
                        return "pong"
                """
            ).strip()
        )
        target = f"{module_path}:{class_name}"
        return AppSpec(
            target=target, file_path=module_path, module=module_name, class_name=class_name
        )

    return _create_app


@pytest.fixture
def publisher_factory(tmp_path: Path):
    """Factory for Publisher instances with isolated state files."""

    def _create(**kwargs):
        return Publisher(
            state_path=tmp_path / "state.json",
            autosave=False,
            **kwargs,
        )

    return _create
