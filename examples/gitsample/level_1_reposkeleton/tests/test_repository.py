"""
Tests for Repository (Level 1 - Skeleton)

These tests verify:
- Repository can be instantiated
- Methods are registered in Switcher
- Methods return correct types (even if skeleton)
- API introspection works
- Dispatch mechanism functions
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repository import Repository


class TestRepositorySkeleton(unittest.TestCase):
    """Test cases for Repository skeleton implementation."""

    def setUp(self):
        """Set up test repository instance."""
        self.repo = Repository(name="test-repo", url="https://github.com/test/repo.git")

    def test_repository_creation(self):
        """Test that Repository can be instantiated."""
        self.assertIsNotNone(self.repo)
        self.assertEqual(self.repo.name, "test-repo")
        self.assertEqual(self.repo.url, "https://github.com/test/repo.git")

    def test_switcher_exists(self):
        """Test that Repository has a Switcher API."""
        self.assertTrue(hasattr(Repository, "api"))
        self.assertIsNotNone(Repository.api)

    def test_branches_registered(self):
        """Test that branches method is registered."""
        description = Repository.api.describe()
        self.assertIn("methods", description)
        self.assertIn("branches", description["methods"])

    def test_history_registered(self):
        """Test that history method is registered."""
        description = Repository.api.describe()
        self.assertIn("history", description["methods"])

    def test_info_registered(self):
        """Test that info method is registered."""
        description = Repository.api.describe()
        self.assertIn("info", description["methods"])

    def test_branches_returns_list(self):
        """Test that branches returns a list (even if empty)."""
        result = Repository.api("branches")(self.repo)
        self.assertIsInstance(result, list)

    def test_history_returns_list(self):
        """Test that history returns a list."""
        result = Repository.api("history")(self.repo, limit=5)
        self.assertIsInstance(result, list)

    def test_history_accepts_limit_parameter(self):
        """Test that history accepts limit parameter."""
        # Should not raise exception
        result = Repository.api("history")(self.repo, limit=20)
        self.assertIsInstance(result, list)

    def test_info_returns_dict(self):
        """Test that info returns a dictionary."""
        result = Repository.api("info")(self.repo)
        self.assertIsInstance(result, dict)

    def test_info_contains_name(self):
        """Test that info dict contains name field."""
        result = Repository.api("info")(self.repo)
        self.assertIn("name", result)
        self.assertEqual(result["name"], "test-repo")

    def test_info_contains_url(self):
        """Test that info dict contains url field."""
        result = Repository.api("info")(self.repo)
        self.assertIn("url", result)
        self.assertEqual(result["url"], "https://github.com/test/repo.git")

    def test_api_introspection_has_methods(self):
        """Test that API introspection returns method information."""
        description = Repository.api.describe()
        methods = description.get("methods", {})
        self.assertEqual(len(methods), 3)  # Should have 3 methods

    def test_method_names_are_concise(self):
        """Test that method names are concise and direct."""
        description = Repository.api.describe()
        methods = description.get("methods", {})

        # Should have these concise names
        self.assertIn("branches", methods)
        self.assertIn("history", methods)
        self.assertIn("info", methods)

    def test_repr(self):
        """Test string representation of Repository."""
        repr_str = repr(self.repo)
        self.assertIn("test-repo", repr_str)
        self.assertIn("https://github.com/test/repo.git", repr_str)

    def test_multiple_instances_isolated(self):
        """Test that multiple Repository instances are isolated."""
        repo1 = Repository("repo1", "https://example.com/repo1.git")
        repo2 = Repository("repo2", "https://example.com/repo2.git")

        self.assertEqual(repo1.name, "repo1")
        self.assertEqual(repo2.name, "repo2")

        # Calling method on repo1 should not affect repo2
        info1 = Repository.api("info")(repo1)
        info2 = Repository.api("info")(repo2)

        self.assertEqual(info1["name"], "repo1")
        self.assertEqual(info2["name"], "repo2")


class TestRepositoryAPIStructure(unittest.TestCase):
    """Test API structure."""

    def test_describe_returns_dict(self):
        """Test that describe() returns a dictionary."""
        description = Repository.api.describe()
        self.assertIsInstance(description, dict)

    def test_describe_has_methods_key(self):
        """Test that describe() includes methods."""
        description = Repository.api.describe()
        self.assertIn("methods", description)

    def test_describe_methods_is_dict(self):
        """Test that methods is a dictionary."""
        description = Repository.api.describe()
        methods = description["methods"]
        self.assertIsInstance(methods, dict)
        self.assertEqual(len(methods), 3)  # 3 methods registered


if __name__ == "__main__":
    unittest.main()
