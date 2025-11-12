"""Test populateDb method."""

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


def test_populate_db(shop):
    """Test that populateDb creates correct number of records."""
    result = shop.populateDb()

    assert result["success"] is True
    assert result["types"] == 4
    assert result["articles"] == 20
    assert result["purchases"] == 120


def test_populate_db_creates_types(shop):
    """Test that populateDb creates article types."""
    shop.populateDb()

    # Check types
    types = shop.db.table("types").list()
    assert types["count"] == 4
    assert types["success"] is True

    # Check type names
    type_names = [t["name"] for t in types["types"]]
    assert "electronics" in type_names
    assert "clothing" in type_names
    assert "books" in type_names
    assert "home" in type_names


def test_populate_db_creates_articles(shop):
    """Test that populateDb creates articles."""
    shop.populateDb()

    # Check articles
    articles = shop.db.table("articles").list()
    assert articles["count"] == 20
    assert articles["success"] is True

    # Check that articles have different types
    article_types = set(a["type"] for a in articles["articles"])
    assert len(article_types) == 4


def test_populate_db_creates_purchases(shop):
    """Test that populateDb creates purchases."""
    shop.populateDb()

    # Check purchases
    purchases = shop.db.table("purchases").list()
    assert purchases["count"] == 120
    assert purchases["success"] is True

    # Check that purchases have valid quantities
    quantities = [p["quantity"] for p in purchases["purchases"]]
    assert all(1 <= q <= 10 for q in quantities)


def test_populate_db_statistics(shop):
    """Test statistics after populating database."""
    shop.populateDb()

    # Get statistics
    stats = shop.db.table("purchases").statistics()

    assert stats["success"] is True
    assert stats["total_purchases"] == 120
    assert stats["total_revenue"] > 0
    assert len(stats["top_articles"]) > 0


def test_populate_db_transaction(shop):
    """Test that populateDb uses transactions correctly."""
    # This should succeed completely or fail completely
    result = shop.populateDb()

    assert result["success"] is True

    # Verify data is actually committed
    types = shop.db.table("types").list()
    articles = shop.db.table("articles").list()
    purchases = shop.db.table("purchases").list()

    assert types["count"] == 4
    assert articles["count"] == 20
    assert purchases["count"] == 120
