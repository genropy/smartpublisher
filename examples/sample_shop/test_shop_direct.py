"""
Test direct (non-published) usage of Shop class.

Tests both:
1. Direct method calls (pythonic usage)
2. Switcher-based calls (by name dispatch)
"""

import pytest
import os
import tempfile
from .shop import Shop


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    # Set environment variable for test database
    os.environ["SHOP_DB_PATH"] = db_path

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def shop(temp_db):
    """Create a Shop instance for testing."""
    return Shop(f"sqlite:{temp_db}")


class TestShopDirectUsage:
    """Test direct (pythonic) usage of Shop."""

    def test_add_type_direct(self, shop):
        """Test adding article type via direct call."""
        result = shop.db.table("types").add("electronics", "Electronic devices")

        assert result["success"]
        assert "id" in result
        assert result["message"] == f"Article type 'electronics' created with id {result['id']}"

    def test_add_type_via_switcher(self, shop):
        """Test adding article type via Switcher dispatch."""
        # Call by name through Switcher
        result = shop.db.table("types").dbop("add")("books", "Books and publications")

        assert result["success"]
        assert "id" in result
        assert "books" in result["message"]

    def test_list_types_direct(self, shop):
        """Test listing types via direct call."""
        # Add some types first
        shop.db.table("types").add("shoes", "Footwear")
        shop.db.table("types").add("clothing", "Apparel")

        result = shop.db.table("types").list()

        assert result["success"]
        assert result["count"] == 2
        assert len(result["types"]) == 2

    def test_list_types_via_switcher(self, shop):
        """Test listing types via Switcher dispatch."""
        shop.db.table("types").add("electronics", "")

        # Call by name through Switcher
        result = shop.db.table("types").dbop("list")()

        assert result["success"]
        assert result["count"] >= 1

    def test_transaction_commit(self, shop):
        """Test manual transaction with autocommit=False."""
        # Add type without autocommit
        result1 = shop.db.table("types").add("electronics", autocommit=False)
        assert result1["success"]

        # Add article without autocommit
        result2 = shop.db.table("articles").add(
            result1["id"], "LAPTOP001", "MacBook Pro", 2499.00, autocommit=False
        )
        assert result2["success"]

        # Manual commit
        shop.db.commit()

        # Verify both were committed
        types = shop.db.table("types").list()
        assert types["count"] == 1

        articles = shop.db.table("articles").list()
        assert articles["count"] == 1


class TestArticlesDirectUsage:
    """Test Articles table direct usage."""

    def test_add_article_direct(self, shop):
        """Test adding article via direct call."""
        # Setup: add type first
        type_result = shop.db.table("types").add("electronics", "")
        type_id = type_result["id"]

        # Add article
        result = shop.db.table("articles").add(type_id, "LAPTOP001", "MacBook Pro 16", 2499.00)

        assert result["success"]
        assert "id" in result
        assert "LAPTOP001" in result["message"]

    def test_add_article_via_switcher(self, shop):
        """Test adding article via Switcher dispatch."""
        type_result = shop.db.table("types").add("books", "")
        type_id = type_result["id"]

        # Call by name through Switcher
        result = shop.db.table("articles").dbop("add")(type_id, "BOOK001", "Python Guide", 29.99)

        assert result["success"]
        assert "id" in result

    def test_pydantic_validation(self, shop):
        """Test that Pydantic validation works."""
        from pydantic import ValidationError

        type_result = shop.db.table("types").add("electronics", "")
        type_id = type_result["id"]

        # Try to add article with negative price - should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            shop.db.table("articles").add(type_id, "BAD001", "Bad Article", -100.00)

        # Check that it's a price validation error
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)


class TestPurchasesDirectUsage:
    """Test Purchases table direct usage."""

    def test_add_purchase_direct(self, shop):
        """Test adding purchase via direct call."""
        # Setup
        type_result = shop.db.table("types").add("electronics", "")
        article_result = shop.db.table("articles").add(
            type_result["id"], "MOUSE001", "Wireless Mouse", 29.99
        )

        # Add purchase
        result = shop.db.table("purchases").add(article_result["id"], 5)

        assert result["success"]
        assert result["quantity"] == 5
        assert result["total"] == 29.99 * 5

    def test_add_purchase_via_switcher(self, shop):
        """Test adding purchase via Switcher dispatch."""
        # Setup
        type_result = shop.db.table("types").add("books", "")
        article_result = shop.db.table("articles").add(
            type_result["id"], "BOOK001", "Python", 39.99
        )

        # Call by name through Switcher
        result = shop.db.table("purchases").dbop("add")(article_result["id"], 3)

        assert result["success"]
        assert result["quantity"] == 3

    def test_statistics_direct(self, shop):
        """Test statistics via direct call."""
        # Setup some data
        type_result = shop.db.table("types").add("electronics", "")
        article_result = shop.db.table("articles").add(
            type_result["id"], "LAPTOP001", "Laptop", 999.00
        )
        shop.db.table("purchases").add(article_result["id"], 2)
        shop.db.table("purchases").add(article_result["id"], 3)

        # Get statistics
        result = shop.db.table("purchases").statistics()

        assert result["success"]
        assert result["total_purchases"] == 2
        assert result["total_revenue"] == 999.00 * 5  # 2 + 3 purchases

    def test_statistics_via_switcher(self, shop):
        """Test statistics via Switcher dispatch."""
        # Setup
        type_result = shop.db.table("types").add("books", "")
        article_result = shop.db.table("articles").add(type_result["id"], "BOOK001", "Book", 29.99)
        shop.db.table("purchases").add(article_result["id"], 1)

        # Call by name through Switcher
        result = shop.db.table("purchases").dbop("statistics")()

        assert result["success"]
        assert result["total_purchases"] >= 1


class TestTransactionManagement:
    """Test transaction management features."""

    def test_autocommit_true(self, shop):
        """Test that autocommit=True commits immediately."""
        result = shop.db.table("types").add("electronics", autocommit=True)
        assert result["success"]

        # Verify it's committed by listing
        types = shop.db.table("types").list()
        assert types["count"] == 1

    def test_autocommit_false_with_manual_commit(self, shop):
        """Test autocommit=False with manual commit."""
        # Add without autocommit
        result = shop.db.table("types").add("electronics", autocommit=False)
        assert result["success"]

        # Manual commit
        shop.db.commit()

        # Verify it's committed
        types = shop.db.table("types").list()
        assert types["count"] == 1

    def test_multiple_operations_single_transaction(self, shop):
        """Test multiple operations in single transaction."""
        # Multiple operations without autocommit
        type1 = shop.db.table("types").add("electronics", autocommit=False)
        type2 = shop.db.table("types").add("books", autocommit=False)
        type3 = shop.db.table("types").add("clothing", autocommit=False)

        assert all([type1["success"], type2["success"], type3["success"]])

        # Single commit
        shop.db.commit()

        # Verify all committed
        types = shop.db.table("types").list()
        assert types["count"] == 3


class TestSwitcherFeatures:
    """Test Switcher-specific features."""

    def test_switcher_entries(self, shop):
        """Test that Switcher reports registered methods."""
        # Get list of registered methods
        entries = shop.db.table("types").dbop.entries()

        assert "add" in entries
        assert "remove" in entries
        assert "list" in entries
        assert "get" in entries

    def test_logging_plugin_configurable(self, shop):
        """Test that logging plugin can be configured."""
        # Logging should be disabled by default (mode='silent')
        assert hasattr(shop.db.table("types").dbop, "logging")

        # Can configure logging
        shop.db.table("types").dbop.logging.configure(mode="verbose")

        # Add a type (logging will be active but we don't check output here)
        result = shop.db.table("types").add("test", "Test type")
        assert result["success"]

        # Reset to silent
        shop.db.table("types").dbop.logging.configure(mode="silent")

    def test_call_method_by_name_with_params(self, shop):
        """Test calling methods by name with various parameter types."""
        # Add type
        type_result = shop.db.table("types").dbop("add")("electronics", "Electronic devices")
        assert type_result["success"]

        # Add article with Field-validated price
        article_result = shop.db.table("articles").dbop("add")(
            type_result["id"], "LAPTOP001", "MacBook Pro", 2499.00
        )
        assert article_result["success"]

        # Add purchase with Field-validated quantity
        purchase_result = shop.db.table("purchases").dbop("add")(article_result["id"], 2)
        assert purchase_result["success"]
        assert purchase_result["total"] == 2499.00 * 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
