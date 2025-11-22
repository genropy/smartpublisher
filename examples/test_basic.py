#!/usr/bin/env python3
"""
Basic test for the new architecture.

Tests:
1. PublishedClass instantiation
2. Handler publication
3. SmartSwitch API access
4. System commands
"""

import sys
from pathlib import Path

# Add src_new to path
sys.path.insert(0, str(Path(__file__).parent))

from example_app import ShopApp


def test_published_class():
    """Test PublishedClass instantiation."""
    print("=" * 70)
    print("Test 1: PublishedClass Instantiation")
    print("=" * 70)

    app = ShopApp()

    # Check root Switcher
    assert hasattr(app, "api"), "App should have 'api' Switcher"
    print("✓ App has root Switcher")

    # Check published_instances
    assert hasattr(app, "published_instances"), "App should have published_instances"
    print("✓ App has published_instances")

    # Check handlers
    assert "shop" in app.published_instances, "Shop handler should be published"
    assert "_system" in app.published_instances, "System handler should be auto-published"
    print(f"✓ Published handlers: {list(app.published_instances.keys())}")

    print()
    return app


def test_smartswitch_api(app):
    """Test SmartSwitch API access."""
    print("=" * 70)
    print("Test 2: SmartSwitch API Access")
    print("=" * 70)

    # Get API schema
    schema = app.api.describe()
    print(f"✓ Root API: {schema.get('name')}")

    # Check children
    children = schema.get("children", {})
    print(f"✓ Children: {list(children.keys())}")

    # Get shop handler schema
    shop_handler = app.published_instances["shop"]
    shop_schema = shop_handler.__class__.api.describe()
    shop_methods = list(shop_schema.get("methods", {}).keys())
    print(f"✓ Shop methods: {shop_methods}")

    print()
    return shop_handler


def test_business_logic(shop_handler):
    """Test business logic execution."""
    print("=" * 70)
    print("Test 3: Business Logic Execution")
    print("=" * 70)

    # Test list products
    result = shop_handler.list()
    assert "products" in result, "List should return products"
    assert result["total"] == 3, "Should have 3 products"
    print(f"✓ list() returned {result['total']} products")

    # Test get product
    result = shop_handler.get(product_id=1)
    assert "product" in result, "Get should return product"
    assert result["product"]["name"] == "Laptop Pro"
    print(f"✓ get(1) returned: {result['product']['name']}")

    # Test search
    result = shop_handler.search(query="Mouse")
    assert result["matches"] == 1, "Should find 1 match"
    print(f"✓ search('Mouse') found {result['matches']} matches")

    # Test update stock
    result = shop_handler.update_stock(product_id=1, quantity=10)
    assert result["status"] == "updated"
    assert result["new_stock"] == 10
    print(f"✓ update_stock(1, 10) updated stock to {result['new_stock']}")

    print()


def test_system_commands(app):
    """Test system commands."""
    print("=" * 70)
    print("Test 4: System Commands")
    print("=" * 70)

    system = app.published_instances["_system"]

    # Test list_handlers
    result = system.list_handlers()
    assert "handlers" in result
    assert "shop" in result["handlers"]
    print(f"✓ list_handlers() found {result['total']} handlers")

    # Test get_handler_info
    result = system.get_handler_info(handler_name="shop")
    assert result["name"] == "shop"
    assert "api_schema" in result
    print("✓ get_handler_info('shop') returned schema")

    # Test get_api_tree
    result = system.get_api_tree()
    assert "name" in result
    assert result["name"] == "root"
    print("✓ get_api_tree() returned root schema")

    print()


def test_switcher_access(app):
    """Test accessing methods via Switcher."""
    print("=" * 70)
    print("Test 5: Switcher Method Access")
    print("=" * 70)

    # Access via SmartSwitch
    shop_handler = app.published_instances["shop"]

    # Get method via Switcher
    list_method = shop_handler.__class__.api.get("list")
    result = list_method(shop_handler)

    assert "products" in result
    print(f"✓ Accessed 'list' via Switcher: {result['total']} products")

    # Get with params
    get_method = shop_handler.__class__.api.get("get")
    result = get_method(shop_handler, product_id=2)

    assert "product" in result
    print(f"✓ Accessed 'get' via Switcher: {result['product']['name']}")

    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SmartPublisher - Basic Architecture Test")
    print("=" * 70)
    print()

    try:
        # Test 1: Instantiation
        app = test_published_class()

        # Test 2: SmartSwitch API
        shop_handler = test_smartswitch_api(app)

        # Test 3: Business Logic
        test_business_logic(shop_handler)

        # Test 4: System Commands
        test_system_commands(app)

        # Test 5: Switcher Access
        test_switcher_access(app)

        # Summary
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Architecture components working:")
        print("  ✓ PublishedClass mixin")
        print("  ✓ Root Switcher")
        print("  ✓ Handler publication")
        print("  ✓ SmartSwitch API introspection")
        print("  ✓ Business logic execution")
        print("  ✓ System commands")
        print("  ✓ Switcher method access")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
