#!/usr/bin/env python3
"""
GitRepos Tutorial - Step 1: Repository Base with Switcher

This example demonstrates the FOUNDATION of smartpublisher:
- How to define a class with Switcher
- Method signatures with type hints
- Using LoggingPlugin to trace method calls
- Dispatch mechanism (even without implementation!)

The methods have 'pass' - they don't do anything yet.
But the dispatch still works, and LoggingPlugin shows what's happening.

Usage:
    # Run as Python library
    python gitrepos_1_repo_base.py

    # Try publishing (in gitrepos_1_published.py)
"""

from smartswitch import Switcher, LoggingPlugin


class Repository:
    """
    Git repository with API methods.

    This is the BASE - methods are defined but not implemented yet (pass).
    We use LoggingPlugin to see the dispatch mechanism in action.
    """

    # Step 1: Define Switcher with prefix
    # The prefix 'repo_' means: repo_get_branches → exposed as 'get_branches'
    api = Switcher(prefix="repo_")

    def __init__(self, name: str, url: str):
        """
        Initialize repository.

        Args:
            name: Repository name
            url: Git URL (e.g., https://github.com/owner/repo.git)
        """
        self.name = name
        self.url = url

        # Add LoggingPlugin to see what methods are called
        # This is GREAT for understanding dispatch!
        Repository.api.add_plugin(LoggingPlugin(name=f"Repo[{name}]"))

    # Step 2: Define methods with @api decorator

    @api
    def repo_get_branches(self) -> list:
        """
        Get repository branches.

        Returns:
            List of branch names
        """
        # Not implemented yet - just a stub
        print(f"    → {self.name}: Would fetch branches from {self.url}")
        return []  # Empty for now

    @api
    def repo_get_commits(self, limit: int = 10) -> list:
        """
        Get commit history.

        Args:
            limit: Number of commits to fetch (default: 10)

        Returns:
            List of commits
        """
        # Not implemented yet - just a stub
        print(f"    → {self.name}: Would fetch {limit} commits")
        return []  # Empty for now

    @api
    def repo_get_info(self) -> dict:
        """
        Get repository information.

        Returns:
            Dictionary with repo info (name, description, stars, etc.)
        """
        # Not implemented yet - just a stub
        print(f"    → {self.name}: Would fetch repo info")
        return {"name": self.name, "url": self.url, "note": "This is stub data - not real API call"}


# ============================================================================
# DEMO: Using Repository as Python Library
# ============================================================================


def demo_python_usage():
    """Demonstrate using Repository as a normal Python class."""

    print("=" * 70)
    print("GitRepos Tutorial - Step 1: Repository Base")
    print("=" * 70)
    print()

    print("📦 Creating Repository instance:")
    print("-" * 70)
    repo = Repository(name="smartpublisher", url="https://github.com/genropy/smartpublisher.git")
    print(f"Repository: {repo.name}")
    print(f"URL: {repo.url}")
    print()

    print("🔍 Testing Method Dispatch (LoggingPlugin shows trace):")
    print("-" * 70)

    print("\n1️⃣  Calling: repo.api.repo_get_branches(repo)")
    result = repo.api.repo_get_branches(repo)
    print(f"   Result: {result}")

    print("\n2️⃣  Calling: repo.api.repo_get_commits(repo, limit=5)")
    result = repo.api.repo_get_commits(repo, limit=5)
    print(f"   Result: {result}")

    print("\n3️⃣  Calling: repo.api.repo_get_info(repo)")
    result = repo.api.repo_get_info(repo)
    print(f"   Result: {result}")

    print()
    print("📋 Available API Methods:")
    print("-" * 70)

    # Use describe() to introspect API
    description = repo.api.describe()

    print(f"Class: {description['class']}")
    print(f"Methods: {len(description['methods'])}")
    print()

    for method_name, method_info in description["methods"].items():
        params = method_info.get("params", [])
        param_str = ", ".join([p["name"] for p in params if p["name"] != "self"])
        print(f"  • {method_name}({param_str})")
        if method_info.get("doc"):
            # Show first line of docstring
            doc_line = method_info["doc"].split("\n")[0].strip()
            print(f"    {doc_line}")

    print()
    print("✅ Key Takeaways:")
    print("-" * 70)
    print("1. Switcher manages method dispatch")
    print("2. @api decorator registers methods")
    print("3. LoggingPlugin traces all calls")
    print("4. Methods can be stubs (pass) - dispatch still works!")
    print("5. describe() provides introspection")
    print()

    print("📌 Next Step:")
    print("-" * 70)
    print("Run: python gitrepos_1_published.py")
    print("     See this published as CLI + HTTP (even with stubs!)")
    print()


if __name__ == "__main__":
    demo_python_usage()
