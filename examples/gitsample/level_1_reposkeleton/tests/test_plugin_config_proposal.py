"""
Tests for proposed plugin configuration enhancements.

These tests demonstrate the DESIRED API for granular plugin configuration.
Currently these tests will FAIL because the feature is not yet implemented.

This file serves as a specification for the enhancement.
"""

import sys
import unittest
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smartswitch import Switcher


class TestProposedConfigAPI(unittest.TestCase):
    """Tests for proposed plugin configuration enhancements."""

    def test_mode_string_with_disabled_flag(self):
        """Test mode string with 'disabled' flag to start plugin disabled."""

        class TestClass:
            api = Switcher()
            # Proposed: 'disabled' flag in mode string
            api.plug("logging", mode="disabled,print")

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

        # Should have NO logging output (plugin disabled by default)
        self.assertEqual(result, "")

        # But can be enabled at runtime
        TestClass.api.set_plugin_enabled(obj, "method_a", "logging", enabled=True)

        output2 = StringIO()
        with redirect_stdout(output2):
            TestClass.api("method_a")(obj)

        result2 = output2.getvalue()
        self.assertIn("→ method_a", result2)

    def test_dict_config_with_wildcard(self):
        """Test dict-based config with '*' wildcard for default."""

        class TestClass:
            api = Switcher()
            # Proposed: dict config with '*' for default
            api.plug(
                "logging",
                config={
                    "*": "disabled",  # Disabled by default
                    "method_a": "enabled,print",  # Enable only for method_a
                },
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
            TestClass.api("method_c")(obj)  # Should NOT log

        result = output.getvalue()

        # Only method_a should have logging
        self.assertIn("→ method_a", result)
        self.assertNotIn("→ method_b", result)
        self.assertNotIn("→ method_c", result)

    def test_dict_config_multiple_methods(self):
        """Test dict config with comma-separated method names."""

        class TestClass:
            api = Switcher()
            # Proposed: comma-separated method names in dict key
            api.plug(
                "logging",
                config={
                    "method_a,method_b": "enabled,print",  # Enable for a and b
                    "method_c": "disabled",  # Disable for c
                },
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
            TestClass.api("method_b")(obj)  # Should log
            TestClass.api("method_c")(obj)  # Should NOT log

        result = output.getvalue()

        self.assertIn("→ method_a", result)
        self.assertIn("→ method_b", result)
        self.assertNotIn("→ method_c", result)

    def test_dict_config_different_modes_per_method(self):
        """Test dict config with different mode flags per method."""

        class TestClass:
            api = Switcher()
            # Proposed: different mode combinations per method
            api.plug(
                "logging",
                config={
                    "*": "enabled,print",  # Print by default
                    "timed_method": "enabled,print,time",  # Add timing
                    "before_only": "enabled,print,before",  # Only before call
                },
            )

            @api
            def normal_method(self):
                return "normal"

            @api
            def timed_method(self):
                return "timed"

            @api
            def before_only(self):
                return "before"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("normal_method")(obj)
            TestClass.api("timed_method")(obj)
            TestClass.api("before_only")(obj)

        result = output.getvalue()

        # normal_method: both before and after (default)
        self.assertIn("→ normal_method", result)
        self.assertIn("← normal_method", result)

        # timed_method: should have timing info
        # Note: exact format depends on LoggingPlugin implementation
        timed_lines = [l for l in result.split("\n") if "timed_method" in l]
        self.assertTrue(any("s)" in l for l in timed_lines))  # Contains timing

        # before_only: only before, not after
        self.assertIn("→ before_only", result)
        # Should NOT have "← before_only" since before flag excludes after
        # (This depends on LoggingPlugin treating 'before' flag as exclusive)

    def test_mixed_mode_and_config(self):
        """Test using both mode (global) and config (specific overrides)."""

        class TestClass:
            api = Switcher()
            # Proposed: mode sets global default, config overrides
            api.plug(
                "logging",
                mode="disabled,print",  # Global default: disabled
                config={"enabled_method": "enabled,print,time"},  # Override for one method
            )

            @api
            def regular_method(self):
                return "regular"

            @api
            def enabled_method(self):
                return "enabled"

        obj = TestClass()
        output = StringIO()

        with redirect_stdout(output):
            TestClass.api("regular_method")(obj)  # Should NOT log (disabled)
            TestClass.api("enabled_method")(obj)  # Should log (enabled override)

        result = output.getvalue()

        self.assertNotIn("→ regular_method", result)
        self.assertIn("→ enabled_method", result)

    def test_per_instance_isolation_with_initial_config(self):
        """Test that initial config doesn't leak between instances."""

        class TestClass:
            api = Switcher()
            api.plug("logging", config={"*": "enabled,print", "method_a": "disabled"})

            @api
            def method_a(self):
                return "A"

        obj1 = TestClass()
        obj2 = TestClass()

        # Both should start with method_a disabled (per initial config)
        output1 = StringIO()
        with redirect_stdout(output1):
            TestClass.api("method_a")(obj1)
        self.assertEqual(output1.getvalue(), "")

        output2 = StringIO()
        with redirect_stdout(output2):
            TestClass.api("method_a")(obj2)
        self.assertEqual(output2.getvalue(), "")

        # Enable for obj1 only
        TestClass.api.set_plugin_enabled(obj1, "method_a", "logging", enabled=True)

        # obj1 should log, obj2 should not
        output3 = StringIO()
        with redirect_stdout(output3):
            TestClass.api("method_a")(obj1)
        self.assertIn("→ method_a", output3.getvalue())

        output4 = StringIO()
        with redirect_stdout(output4):
            TestClass.api("method_a")(obj2)
        self.assertEqual(output4.getvalue(), "")


if __name__ == "__main__":
    # Run tests - they will fail until feature is implemented
    print("=" * 70)
    print("PROPOSED FEATURE TESTS - Expected to FAIL")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)
