"""
Tests for implemented plugin configuration (smartswitch v0.10.0+).

These tests demonstrate the ACTUAL API implemented in smartswitch for granular
plugin configuration. All tests should PASS with smartswitch >= 0.10.0.

For comparison with original proposal, see test_plugin_config_proposal.py
"""

import sys
import unittest
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smartswitch import Switcher


class TestImplementedConfigAPI(unittest.TestCase):
    """Tests for implemented plugin configuration API."""

    def test_flags_with_enabled(self):
        """Test basic flags parameter with enabled flag."""

        class TestClass:
            api = Switcher()
            # Default is before=True, after=False
            api.plug("logging", flags="print,enabled,after")

            @api
            def method_a(self):
                return "A"

            @api
            def method_b(self):
                return "B"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("method_a")(obj)
            TestClass.api("method_b")(obj)

        result = output.getvalue()

        # Both methods should have logging (enabled globally)
        self.assertIn("→ method_a", result)
        self.assertIn("← method_a", result)
        self.assertIn("→ method_b", result)
        self.assertIn("← method_b", result)

    def test_default_disabled(self):
        """Test that plugin is disabled by default (opt-in behavior)."""

        class TestClass:
            api = Switcher()
            # No enabled flag - should be disabled
            api.plug("logging", flags="print")

            @api
            def method_a(self):
                return "A"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("method_a")(obj)

        result = output.getvalue()

        # Should have NO output (disabled by default)
        self.assertEqual(result, "")

    def test_method_config_disable_specific(self):
        """Test method_config to disable specific methods."""

        class TestClass:
            api = Switcher()
            api.plug(
                "logging",
                flags="print,enabled",
                method_config={"method_b": "enabled:off"},  # Disable for method_b
            )

            @api
            def method_a(self):
                return "A"

            @api
            def method_b(self):
                return "B"

            @api
            def method_c(self):
                return "C"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("method_a")(obj)  # Should log
            TestClass.api("method_b")(obj)  # Should NOT log
            TestClass.api("method_c")(obj)  # Should log

        result = output.getvalue()

        # method_a and method_c should log, method_b should not
        self.assertIn("→ method_a", result)
        self.assertNotIn("→ method_b", result)
        self.assertIn("→ method_c", result)

    def test_method_config_comma_separated(self):
        """Test method_config with comma-separated method names."""

        class TestClass:
            api = Switcher()
            api.plug(
                "logging",
                flags="print,enabled",
                method_config={"method_a,method_b": "enabled:off"},  # Disable both
            )

            @api
            def method_a(self):
                return "A"

            @api
            def method_b(self):
                return "B"

            @api
            def method_c(self):
                return "C"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("method_a")(obj)  # Should NOT log
            TestClass.api("method_b")(obj)  # Should NOT log
            TestClass.api("method_c")(obj)  # Should log

        result = output.getvalue()

        self.assertNotIn("→ method_a", result)
        self.assertNotIn("→ method_b", result)
        self.assertIn("→ method_c", result)

    def test_method_config_override_flags(self):
        """Test method_config overriding specific flags."""

        class TestClass:
            api = Switcher()
            api.plug(
                "logging",
                flags="print,enabled,after",  # Global: before + after
                method_config={
                    "method_a": "before:off,after,time",  # Only after + time
                    "method_b": "before,after:off",  # Only before
                },
            )

            @api
            def method_a(self):
                return "A"

            @api
            def method_b(self):
                return "B"

            @api
            def normal(self):
                return "N"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("method_a")(obj)
            TestClass.api("method_b")(obj)
            TestClass.api("normal")(obj)

        result = output.getvalue()

        # method_a: no before, has after (with timing)
        self.assertNotIn("→ method_a", result)
        self.assertIn("← method_a", result)
        # Check for timing format (has 's)' somewhere in line with method_a)
        lines_with_a = [l for l in result.split("\n") if "method_a" in l]
        self.assertTrue(any("s)" in l for l in lines_with_a))

        # method_b: has before, no after
        self.assertIn("→ method_b", result)
        self.assertNotIn("← method_b", result)

        # normal: both before and after (default)
        self.assertIn("→ normal", result)
        self.assertIn("← normal", result)

    def test_mixed_global_and_method_specific(self):
        """Test mixed global flags and method-specific overrides."""

        class TestClass:
            api = Switcher()
            api.plug(
                "logging",
                flags="print,enabled,after",  # Global: enabled with after
                method_config={
                    "debug": "after:off,before,time",  # Override: before + time only
                    "silent": "enabled:off",  # Disable completely
                },
            )

            @api
            def normal(self):
                return "normal"

            @api
            def debug(self):
                return "debug"

            @api
            def silent(self):
                return "silent"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("normal")(obj)  # Should have after
            TestClass.api("debug")(obj)  # Should have before + time only
            TestClass.api("silent")(obj)  # Should NOT log

        result = output.getvalue()

        # normal: has after (from global)
        self.assertIn("← normal", result)

        # debug: has before + time, no after
        self.assertIn("→ debug", result)
        self.assertNotIn("← debug", result)

        # silent: no output at all
        self.assertNotIn("silent", result)


if __name__ == "__main__":
    print("=" * 70)
    print("IMPLEMENTED API TESTS - smartswitch v0.10.0+")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)
