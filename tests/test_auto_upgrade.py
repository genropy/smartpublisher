"""
Test auto-upgrade from plain Switcher to ApiSwitcher during publish().

This tests Issue #5: Users developing with smartswitch can use plain Switcher,
and smpub automatically upgrades it to ApiSwitcher when publishing.
"""

import pytest
from smartswitch import Switcher
from smpub import Publisher
from smpub.apiswitcher import ApiSwitcher  # Internal - for testing only


class PlainSwitcherHandler:
    """Handler using plain smartswitch.Switcher (not ApiSwitcher)."""

    api = Switcher(prefix="user_")

    def __init__(self):
        self.data = {}

    @api
    def user_add(self, name: str, age: int = 25):
        """Add a user.

        Args:
            name: User's name
            age: User's age
        """
        self.data[name] = age
        return f"Added {name}, age {age}"

    @api
    async def user_fetch(self, name: str):
        """Fetch a user (async method).

        Args:
            name: User's name
        """
        return self.data.get(name, "Not found")


class TestAutoUpgrade:
    """Test automatic Switcher → ApiSwitcher upgrade."""

    def test_plain_switcher_upgraded_to_apiswitcher(self):
        """Should auto-upgrade plain Switcher to ApiSwitcher during publish()."""

        class TestApp(Publisher):
            def initialize(self):
                self.users = PlainSwitcherHandler()
                self.publish("users", self.users)

        # Before publish: class has plain Switcher
        assert isinstance(PlainSwitcherHandler.api, Switcher)
        original_api = PlainSwitcherHandler.api

        # Create app and publish
        app = TestApp()

        # After publish: class api should be upgraded to ApiSwitcher
        assert isinstance(PlainSwitcherHandler.api, ApiSwitcher)
        assert not isinstance(original_api, ApiSwitcher)  # Original was plain

        # Upgraded ApiSwitcher should have same prefix
        assert app.users.__class__.api.prefix == "user_"

        # Handlers should be preserved
        assert "add" in app.users.__class__.api._handlers
        assert "fetch" in app.users.__class__.api._handlers

    def test_pydantic_models_generated_after_upgrade(self):
        """Should generate Pydantic models for methods after upgrade."""

        class TestApp(Publisher):
            def initialize(self):
                self.users = PlainSwitcherHandler()
                self.publish("users", self.users)

        app = TestApp()
        upgraded_api = app.users.__class__.api

        # Check Pydantic models were generated
        assert isinstance(upgraded_api, ApiSwitcher)
        assert "add" in upgraded_api._pydantic_models
        assert "fetch" in upgraded_api._pydantic_models

        # Verify model structure for 'add'
        add_model = upgraded_api._pydantic_models["add"]
        assert add_model is not None
        fields = add_model.model_fields
        assert "name" in fields
        assert "age" in fields
        assert fields["age"].default == 25  # Default value preserved

    def test_apiswitcher_not_upgraded_again(self):
        """Should not upgrade if handler already uses ApiSwitcher."""

        class ApiSwitcherHandler:
            """Handler already using ApiSwitcher."""

            api = ApiSwitcher(prefix="api_")

            @api
            def api_test(self, value: str):
                """Test method."""
                return value

        class TestApp(Publisher):
            def initialize(self):
                self.handler = ApiSwitcherHandler()
                self.publish("handler", self.handler)

        original_api = ApiSwitcherHandler.api
        app = TestApp()

        # Should be the same instance (not replaced)
        assert app.handler.__class__.api is original_api

    def test_handler_without_api_not_affected(self):
        """Should not fail if handler has no 'api' attribute."""

        class NoApiHandler:
            """Handler without api attribute."""

            def __init__(self):
                self.value = 42

        class TestApp(Publisher):
            def initialize(self):
                self.handler = NoApiHandler()
                self.publish("handler", self.handler)

        # Should not raise
        app = TestApp()
        assert app.handler.value == 42

    def test_methods_work_after_upgrade(self):
        """Should be able to call methods after auto-upgrade."""

        class TestApp(Publisher):
            def initialize(self):
                self.users = PlainSwitcherHandler()
                self.publish("users", self.users)

        app = TestApp()

        # Call sync method
        result = app.users.user_add("Alice", 30)
        assert result == "Added Alice, age 30"
        assert app.users.data["Alice"] == 30

        # Call async method (should work in sync context via smartasync)
        result = app.users.user_fetch("Alice")
        assert result == 30

    @pytest.mark.asyncio
    async def test_async_methods_work_after_upgrade(self):
        """Should be able to await async methods after auto-upgrade."""

        class TestApp(Publisher):
            def initialize(self):
                self.users = PlainSwitcherHandler()
                self.publish("users", self.users)

        app = TestApp()

        # Add data (must await sync method in async context)
        await app.users.user_add("Bob", 25)

        # Call async method with await
        result = await app.users.user_fetch("Bob")
        assert result == 25
