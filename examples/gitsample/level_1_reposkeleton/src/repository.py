"""
Repository - Skeleton Version (Level 1)

This is a SKELETON implementation - methods are defined but not implemented (pass).
The goal is to show:
- How to structure a class with Switcher
- Method signatures with type hints
- How dispatch works even without implementation

The Repository class will eventually call GitHub API to get repo info,
but for now it just has the structure.
"""

from __future__ import annotations

from typing import Annotated

from smartswitch import Switcher


class Repository:
    """
    Git repository with API methods (skeleton version).

    This class defines the API surface but doesn't implement the methods yet.
    All methods return placeholder data or None.

    Attributes:
        name: Repository name
        url: Git repository URL (e.g., https://github.com/owner/repo.git)
    """

    # Define Switcher for method dispatch
    api = Switcher()
    api.plug("logging", flags="print,enabled,time")

    def __init__(self, name: str, url: str):
        """
        Initialize repository.

        Args:
            name: Repository name
            url: Git repository URL
        """
        self.name = name
        self.url = url

    @api
    def branches(self) -> list[str]:
        """
        Get list of branches in repository.

        Returns:
            List of branch names

        Note:
            This is a skeleton - returns empty list
        """
        # TODO: Implement GitHub API call
        return []

    @api
    def history(
        self,
        limit: Annotated[int, "Maximum number of commits to return"] = 10,
        author: Annotated[str | None, "Filter by author name"] = None,
        pattern: Annotated[str | None, "Regex pattern to filter commit messages"] = None,
    ) -> list[dict[str, str]]:
        """
        Get commit history with optional filtering.

        Args:
            limit: Maximum number of commits to return (default: 10)
            author: Filter commits by author name (optional)
            pattern: Regex pattern to filter commit messages (optional)

        Returns:
            List of commit dictionaries with hash, author, date, message

        Note:
            This is a skeleton - returns empty list
        """
        # TODO: Implement GitHub API call with filters
        return []

    @api
    def info(self) -> dict[str, str]:
        """
        Get repository information.

        Returns:
            Dictionary with repo metadata (name, description, stars, etc.)

        Note:
            This is a skeleton - returns minimal stub data
        """
        # TODO: Implement GitHub API call
        return {
            "name": self.name,
            "url": self.url,
            "note": "This is skeleton data - not real API response",
        }

    def __repr__(self):
        """String representation of Repository."""
        return f"Repository(name='{self.name}', url='{self.url}')"


if __name__ == "__main__":
    # Simple example of Repository usage
    repo = Repository(name="smartpublisher", url="https://github.com/genropy/smartpublisher.git")

    print("Testing Repository methods...\n")

    Repository.api("branches")(repo)
    Repository.api("history")(repo, limit=5)
    Repository.api("info")(repo)
