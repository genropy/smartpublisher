"""Test ApiSwitcher with async methods and smartasync integration."""

import asyncio
import pytest
from smpub import PublishedClass, ApiSwitcher


class AsyncHandler(PublishedClass):
    """Handler with both sync and async methods."""

    api = ApiSwitcher(prefix="handler_")

    def __init__(self):
        self.call_count = 0

    @api
    def sync_method(self, value: str) -> str:
        """Sync method."""
        self.call_count += 1
        return f"Sync: {value}"

    @api
    async def async_method(self, value: str) -> str:
        """Async method - should be auto-wrapped with @smartasync."""
        await asyncio.sleep(0.01)
        self.call_count += 1
        return f"Async: {value}"

    @api
    async def async_with_default(self, value: str, count: int = 5) -> str:
        """Async method with default parameter."""
        await asyncio.sleep(0.01)
        return f"Value: {value}, Count: {count}"


def test_sync_method_works():
    """Test that sync methods work normally."""
    handler = AsyncHandler()
    result = handler.sync_method("test")
    assert result == "Sync: test"
    assert handler.call_count == 1


def test_async_method_in_sync_context():
    """Test that async methods can be called without await in sync context."""
    handler = AsyncHandler()

    # Call async method without await - should work thanks to @smartasync
    result = handler.async_method("test")
    assert result == "Async: test"
    assert handler.call_count == 1


def test_async_method_multiple_calls():
    """Test multiple calls to async method in sync context."""
    handler = AsyncHandler()

    result1 = handler.async_method("first")
    assert result1 == "Async: first"
    assert handler.call_count == 1

    result2 = handler.async_method("second")
    assert result2 == "Async: second"
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_async_method_in_async_context():
    """Test that async methods work with await in async context."""
    handler = AsyncHandler()

    # Call async method with await in async context
    result = await handler.async_method("test")
    assert result == "Async: test"
    assert handler.call_count == 1


@pytest.mark.asyncio
async def test_async_method_with_defaults_in_async_context():
    """Test async method with default parameters in async context."""
    handler = AsyncHandler()

    # With default
    result1 = await handler.async_with_default("test")
    assert result1 == "Value: test, Count: 5"

    # Override default
    result2 = await handler.async_with_default("test", count=10)
    assert result2 == "Value: test, Count: 10"


def test_async_method_with_defaults_in_sync_context():
    """Test async method with default parameters in sync context."""
    handler = AsyncHandler()

    # Reset smartasync cache to ensure clean state
    if hasattr(handler.async_with_default, "_smartasync_reset_cache"):
        handler.async_with_default._smartasync_reset_cache()

    # With default
    result1 = handler.async_with_default("test")
    assert result1 == "Value: test, Count: 5"

    # Override default
    result2 = handler.async_with_default("test", count=10)
    assert result2 == "Value: test, Count: 10"


def test_pydantic_model_created_for_async_method():
    """Test that Pydantic models are created for async methods."""
    handler = AsyncHandler()
    api_switcher = handler.api

    # Check that Pydantic model exists for async_method
    model = api_switcher.get_pydantic_model("async_method")
    assert model is not None

    # Check model fields
    fields = model.model_fields
    assert "value" in fields
    assert fields["value"].annotation is str


def test_pydantic_model_created_for_async_with_defaults():
    """Test that Pydantic models correctly handle defaults in async methods."""
    handler = AsyncHandler()
    api_switcher = handler.api

    # Check that Pydantic model exists
    model = api_switcher.get_pydantic_model("async_with_default")
    assert model is not None

    # Check model fields
    fields = model.model_fields
    assert "value" in fields
    assert "count" in fields

    # Check default value
    assert fields["count"].default == 5


@pytest.mark.asyncio
async def test_mixed_sync_async_calls():
    """Test mixing sync and async method calls in async context.

    With bidirectional smartasync support, both sync and async methods
    must be awaited in async contexts.
    """
    handler = AsyncHandler()

    # Sync method in async context - must await (runs in thread)
    result1 = await handler.sync_method("sync")
    assert result1 == "Sync: sync"
    assert handler.call_count == 1

    # Async method in async context - must await (native coroutine)
    result2 = await handler.async_method("async")
    assert result2 == "Async: async"
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_sync_method_non_blocking_in_async():
    """Test that sync methods don't block event loop in async context."""
    import time

    class BlockingHandler(PublishedClass):
        api = ApiSwitcher()

        def __init__(self):
            self.call_times = []

        @api
        def blocking_method(self, duration: float):
            """Sync method that blocks for duration seconds."""
            time.sleep(duration)
            self.call_times.append(time.time())
            return f"Slept for {duration}s"

    handler = BlockingHandler()

    # Call two blocking methods concurrently
    # If they run in threads, they should complete in ~0.1s total
    # If they block, they would take ~0.2s total
    start = time.time()
    results = await asyncio.gather(
        handler.blocking_method(0.1),
        handler.blocking_method(0.1)
    )
    elapsed = time.time() - start

    assert len(results) == 2
    assert all("Slept for 0.1s" in r for r in results)
    # Should complete in ~0.1s (concurrent) not ~0.2s (sequential)
    assert elapsed < 0.15, f"Expected < 0.15s, got {elapsed:.3f}s (blocking detected!)"


def test_cache_reset_available():
    """Test that smartasync cache reset is available."""
    handler = AsyncHandler()

    # All methods should have _smartasync_reset_cache attribute
    assert hasattr(handler.async_method, "_smartasync_reset_cache")
    assert hasattr(handler.sync_method, "_smartasync_reset_cache")

    # Test cache reset
    handler.async_method._smartasync_reset_cache()
    result = handler.async_method("test")
    assert result == "Async: test"
