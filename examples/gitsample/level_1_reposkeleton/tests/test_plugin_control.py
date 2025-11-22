"""
Tests for runtime plugin control.

These tests verify the SmartSwitch plugin control system:
- Enable/disable plugins at runtime
- Control per instance, method, and plugin
- Modify plugin parameters at runtime
"""

import sys
import unittest
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repository import Repository


class TestPluginRuntimeControl(unittest.TestCase):
    """Test runtime control of plugins."""

    def setUp(self):
        """Create a test repository instance."""
        self.repo = Repository("test-repo", "https://github.com/test/repo.git")

    def test_plugin_can_be_disabled_per_method(self):
        """Test that plugin can be disabled for specific method."""
        # Disable logging for history method
        Repository.api.set_plugin_enabled(self.repo, "history", "logging", enabled=False)

        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            # branches should have logging
            Repository.api("branches")(self.repo)
            # history should NOT have logging
            Repository.api("history")(self.repo, limit=5)
            # info should have logging
            Repository.api("info")(self.repo)

        result = output.getvalue()

        # Check that branches and info have logging
        self.assertIn("→ branches", result)
        self.assertIn("← branches", result)
        self.assertIn("→ info", result)
        self.assertIn("← info", result)

        # Check that history does NOT have logging
        self.assertNotIn("→ history", result)
        self.assertNotIn("← history", result)

    def test_plugin_can_be_reenabled(self):
        """Test that plugin can be re-enabled after being disabled."""
        # Disable
        Repository.api.set_plugin_enabled(self.repo, "history", "logging", enabled=False)

        # Verify disabled
        output1 = StringIO()
        with redirect_stdout(output1):
            Repository.api("history")(self.repo, limit=5)
        self.assertNotIn("→ history", output1.getvalue())

        # Re-enable
        Repository.api.set_plugin_enabled(self.repo, "history", "logging", enabled=True)

        # Verify enabled
        output2 = StringIO()
        with redirect_stdout(output2):
            Repository.api("history")(self.repo, limit=5)
        self.assertIn("→ history", output2.getvalue())

    def test_plugin_control_per_instance(self):
        """Test that plugin control is per-instance."""
        repo1 = Repository("repo1", "https://example.com/repo1.git")
        repo2 = Repository("repo2", "https://example.com/repo2.git")

        # Disable logging for repo1's history only
        Repository.api.set_plugin_enabled(repo1, "history", "logging", enabled=False)

        # Test repo1 - should have NO logging for history
        output1 = StringIO()
        with redirect_stdout(output1):
            Repository.api("history")(repo1, limit=5)
        self.assertNotIn("→ history", output1.getvalue())

        # Test repo2 - should STILL have logging for history
        output2 = StringIO()
        with redirect_stdout(output2):
            Repository.api("history")(repo2, limit=5)
        self.assertIn("→ history", output2.getvalue())

    def test_check_plugin_enabled_status(self):
        """Test is_plugin_enabled returns correct status."""
        # Initially enabled (default)
        self.assertTrue(Repository.api.is_plugin_enabled(self.repo, "branches", "logging"))

        # After disabling
        Repository.api.set_plugin_enabled(self.repo, "branches", "logging", enabled=False)
        self.assertFalse(Repository.api.is_plugin_enabled(self.repo, "branches", "logging"))

        # After re-enabling
        Repository.api.set_plugin_enabled(self.repo, "branches", "logging", enabled=True)
        self.assertTrue(Repository.api.is_plugin_enabled(self.repo, "branches", "logging"))


if __name__ == "__main__":
    unittest.main()
