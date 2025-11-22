#!/usr/bin/env python3
"""
GitRepos Tutorial - Step 1: Published Version

This demonstrates that smartpublisher works EVEN WITH STUB METHODS!

The Repository class from gitrepos_1_repo_base.py has methods with 'pass',
but we can still publish it and get:
- CLI interface (automatic!)
- HTTP API (automatic!)
- OpenAPI/Swagger docs (automatic!)

The LoggingPlugin will show every method call.

Usage:
    # CLI mode
    python gitrepos_1_published.py repo get-branches
    python gitrepos_1_published.py repo get-commits --limit 5
    python gitrepos_1_published.py repo get-info

    # HTTP mode (no args = start server)
    python gitrepos_1_published.py
    # Then open: http://localhost:8000/docs

Key Learning:
    You can develop with stubs/mocks and still have working CLI/HTTP!
    This is great for:
    - TDD (Test-Driven Development)
    - API-first design
    - Prototyping
    - Team collaboration (backend/frontend can work in parallel)
"""

from smartpublisher import Publisher
from gitrepos_1_repo_base import Repository


class GitReposApp(Publisher):
    """
    Published version of Repository.

    Notice: This is TINY (~10 lines)!
    All the work is in Repository class (the library).
    Publisher just exposes it.
    """

    def on_init(self):
        """Initialize and publish repository."""

        # Create repository instance
        repo = Repository(
            name="smartpublisher", url="https://github.com/genropy/smartpublisher.git"
        )

        # Publish it!
        # This makes all @api methods available via CLI and HTTP
        self.publish("repo", repo)


if __name__ == "__main__":
    print()
    print("=" * 70)
    print("GitRepos Tutorial - Step 1: Published (with stubs + logging)")
    print("=" * 70)
    print()
    print("💡 This example shows smartpublisher works even with stub methods!")
    print()
    print("Try these commands:")
    print("  python gitrepos_1_published.py repo get-branches")
    print("  python gitrepos_1_published.py repo get-commits --limit 5")
    print("  python gitrepos_1_published.py repo get-info")
    print()
    print("Or start HTTP server:")
    print("  python gitrepos_1_published.py")
    print("  Then: http://localhost:8000/docs")
    print()
    print("-" * 70)
    print()

    app = GitReposApp()
    app.run()
