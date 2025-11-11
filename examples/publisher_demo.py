"""
Publisher Demo Application

Demonstrates the Publisher class functionality with FastAPI integration.
"""

import sys
from pathlib import Path

# Add refactored_classes to path
sys.path.insert(0, str(Path(__file__).parent.parent / "refactored_classes"))

from storage_manager import StorageManager
from publisher import Publisher


class PublisherApp(Publisher):
    """
    Application that extends Publisher functionality.
    """

    def __init__(self):
        """
        Initialize PublisherApp with StorageManager.
        """
        self.storage = StorageManager()
        self.publish("storage", self.storage)


def main():
    """
    Demo application for Publisher.
    """
    app = PublisherApp()
    app.run()


if __name__ == "__main__":
    main()
