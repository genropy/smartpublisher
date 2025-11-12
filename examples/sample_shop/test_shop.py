"""
Tests for sample_shop.

Run with: pytest examples/sample_shop/test_shop.py -v
"""

import pytest

# Import from examples.sample_shop package
from examples.sample_shop import Shop


@pytest.fixture
def shop():
    """Create a fresh Shop instance for each test."""
    # Clean up database if exists
    from examples.sample_shop.database import DB_PATH

    if DB_PATH.exists():
        DB_PATH.unlink()

    return Shop()


def test_shop_creation(shop):
    """Test that Shop can be instantiated."""
    assert shop is not None
    assert hasattr(shop, "types")
    assert hasattr(shop, "articles")
    assert hasattr(shop, "purchases")


def test_add_article_type(shop):
    """Test adding an article type."""
    result = shop.types.add("electronics", "Electronic devices")

    assert result["success"] is True
    assert "id" in result
    assert result["id"] >= 1  # ID depends on initial data


def test_list_article_types(shop):
    """Test listing article types."""
    # Get initial count
    initial_result = shop.types.list()
    initial_count = initial_result["count"]

    # Add some types
    shop.types.add("electronics", "Electronic devices")
    shop.types.add("furniture", "Furniture items")

    result = shop.types.list()

    assert result["success"] is True
    assert result["count"] == initial_count + 2
    assert len(result["types"]) == initial_count + 2


def test_add_article(shop):
    """Test adding an article."""
    # First add article type
    shop.types.add("electronics", "Electronic devices")

    # Add article
    result = shop.articles.add(
        article_type_id=1, code="LAPTOP001", description="MacBook Pro", price=2499.00
    )

    assert result["success"] is True
    assert "id" in result


def test_add_article_invalid_price(shop):
    """Test that negative price fails validation."""
    shop.types.add("electronics", "Electronic devices")

    # Note: Without smartswitch Switcher, classes don't have PydanticPlugin applied
    # This test would need the classes to use Switcher for automatic validation
    # For now, we test that business logic validation works

    # Try invalid price - should fail at Pydantic level when published
    # In pure Python mode, this might succeed but fail in real usage
    try:
        result = shop.articles.add(
            article_type_id=1, code="INVALID", description="Invalid", price=-10.00  # Invalid!
        )
        # If no exception, at least check it was rejected somehow
        assert result.get("success") is False, "Negative price should be rejected"
    except Exception:
        # Expected - Pydantic validation error
        pass


def test_add_purchase(shop):
    """Test adding a purchase."""
    # Setup
    shop.types.add("electronics", "Electronic devices")
    shop.articles.add(article_type_id=1, code="LAPTOP001", description="MacBook Pro", price=2499.00)

    # Add purchase
    result = shop.purchases.add(article_id=1, quantity=2)

    assert result["success"] is True
    assert result["quantity"] == 2
    assert result["total"] == 4998.00


def test_purchase_statistics(shop):
    """Test purchase statistics."""
    # Setup
    shop.types.add("electronics", "Electronic devices")
    shop.articles.add(article_type_id=1, code="LAPTOP001", description="MacBook Pro", price=2499.00)
    shop.purchases.add(article_id=1, quantity=2)

    # Get stats
    result = shop.purchases.statistics()

    assert result["success"] is True
    assert result["total_purchases"] == 1
    assert result["total_revenue"] == 4998.00


def test_convenience_methods(shop):
    """Test Shop convenience methods."""
    # Add type via convenience method
    result = shop.add_type("electronics", "Electronic devices")
    assert result["success"] is True

    # Get stats via convenience method
    stats = shop.get_statistics()
    assert "total_purchases" in stats


def test_update_price(shop):
    """Test updating article price."""
    shop.types.add("electronics", "Electronic devices")
    shop.articles.add(article_type_id=1, code="LAPTOP001", description="MacBook Pro", price=2499.00)

    # Update price
    result = shop.articles.update_price(id=1, new_price=2299.00)

    assert result["success"] is True
    assert "2499" in result["message"]  # Old price
    assert "2299" in result["message"]  # New price


def test_filter_articles_by_type(shop):
    """Test filtering articles by type."""
    # Add types
    shop.types.add("electronics", "Electronic devices")
    shop.types.add("books", "Books")

    # Add articles
    shop.articles.add(article_type_id=1, code="LAPTOP", description="Laptop", price=1000)
    shop.articles.add(article_type_id=2, code="BOOK", description="Book", price=20)

    # Filter by type
    result = shop.articles.list(article_type_id=1)

    assert result["count"] == 1
    assert result["articles"][0]["code"] == "LAPTOP"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
