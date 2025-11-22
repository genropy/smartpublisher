#!/usr/bin/env python3
"""
Published Repository App

This demonstrates the MAGIC of smartpublisher:
- Take the Repository library (from ../src/)
- Publish it with ~10 lines of code
- Get CLI + HTTP + OpenAPI automatically!

Even though Repository methods are skeletons, the published app works!

Usage:
    # CLI mode
    python main.py repo branches
    python main.py repo history --limit 5
    python main.py repo info

    # HTTP mode (no args = start server)
    python main.py
    # Then: http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smartpublisher import Publisher
from repository import Repository


class RepoApp(Publisher):
    """
    Published Repository application.

    Notice: This is TINY!
    - The library (Repository) does the work
    - Publisher just exposes it

    This is the smartpublisher philosophy:
    1. Write your library (with SmartSwitch)
    2. Publish with ~10 lines
    3. Get CLI + HTTP for free
    """

    def on_init(self):
        """Initialize and publish repository."""

        # Create a Repository instance
        # (In a real app, you might load config or take CLI args)
        repo = Repository(
            name="smartpublisher", url="https://github.com/genropy/smartpublisher.git"
        )

        # Publish it!
        # This single line exposes all @api methods via CLI and HTTP
        self.publish("repo", repo)


def main():
    """Entry point with helpful banner."""

    print()
    print("=" * 70)
    print("Level 1: Repository Skeleton - Published App")
    print("=" * 70)
    print()
    print("💡 This app publishes the Repository skeleton as CLI + HTTP")
    print()
    print("Try these commands:")
    print("  python main.py repo branches")
    print("  python main.py repo history --limit 5")
    print("  python main.py repo info")
    print()
    print("Or start HTTP server:")
    print("  python main.py")
    print("  Then open: http://localhost:8000/docs")
    print()
    print("Even with skeleton methods, you get a working interface!")
    print("-" * 70)
    print()

    # Run the app
    app = RepoApp()
    app.run()


if __name__ == "__main__":
    main()
