#!/usr/bin/env python3
"""Repository Library Usage Example"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repository import Repository


class Application:
    """Application that uses Repository."""

    def __init__(self, name: str, url: str):
        self.repo = Repository(name=name, url=url)


if __name__ == "__main__":
    app = Application(name="smartpublisher", url="https://github.com/genropy/smartpublisher.git")
