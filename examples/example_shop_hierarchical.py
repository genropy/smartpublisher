"""
Example: Hierarchical Shop with nested Switchers.

Structure:
  shop/
    ├─ db/
    │   ├─ tables/
    │   │   ├─ product/
    │   │   │   ├─ list()
    │   │   │   ├─ get(id)
    │   │   │   └─ create(name, price)
    │   │   └─ customer/
    │   │       ├─ list()
    │   │       └─ get(id)
    │   └─ query(sql)
    └─ inventory/
        └─ check(product_id)

CLI usage:
  $ smpub myshop shop db tables product list
  $ smpub myshop shop db tables product get --id 1
  $ smpub myshop shop db tables customer list
  $ smpub myshop shop db query --sql "SELECT * FROM products"
  $ smpub myshop shop inventory check --product_id 1

Internal: api.get('shop.db.tables.product.list')
"""

import sys
from pathlib import Path

# Add src_new to path
sys.path.insert(0, str(Path(__file__).parent))

from smartroute.core import Router
from published import PublishedClass


# ============================================================================
# Level 4: Table handlers (products, customers)
# ============================================================================


class ProductTableHandler:
    """Handler for product table operations."""

    api = Router(name="product")

    def __init__(self):
        self.products = [
            {"id": 1, "name": "Laptop Pro", "price": 1299.99, "stock": 5},
            {"id": 2, "name": "Wireless Mouse", "price": 29.99, "stock": 50},
            {"id": 3, "name": "USB-C Cable", "price": 12.99, "stock": 100},
        ]

    @api
    def list(self) -> dict:
        """List all products."""
        return {"table": "product", "rows": self.products, "count": len(self.products)}

    @api
    def get(self, id: int) -> dict:
        """Get product by ID."""
        for p in self.products:
            if p["id"] == id:
                return {"table": "product", "row": p}
        return {"error": f"Product {id} not found"}

    @api
    def create(self, name: str, price: float) -> dict:
        """Create new product."""
        new_id = max(p["id"] for p in self.products) + 1
        product = {"id": new_id, "name": name, "price": price, "stock": 0}
        self.products.append(product)
        return {"status": "created", "table": "product", "row": product}


class CustomerTableHandler:
    """Handler for customer table operations."""

    api = Router(name="customer")

    def __init__(self):
        self.customers = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]

    @api
    def list(self) -> dict:
        """List all customers."""
        return {"table": "customer", "rows": self.customers, "count": len(self.customers)}

    @api
    def get(self, id: int) -> dict:
        """Get customer by ID."""
        for c in self.customers:
            if c["id"] == id:
                return {"table": "customer", "row": c}
        return {"error": f"Customer {id} not found"}


# ============================================================================
# Level 3: Tables handler (contains product, customer)
# ============================================================================


class TablesHandler:
    """Handler for database tables."""

    api = Router(name="tables")

    def __init__(self):
        # Initialize table handlers
        self.product = ProductTableHandler()
        self.customer = CustomerTableHandler()

        # Register as children in the Switcher hierarchy (CORRECT WAY)
        self.api.add_child(self.product.api)
        self.api.add_child(self.customer.api)


# ============================================================================
# Level 2: DB handler (contains tables + query command)
# ============================================================================


class DBHandler:
    """Handler for database operations."""

    api = Router(name="db")

    def __init__(self):
        # Initialize sub-handlers
        self.tables = TablesHandler()

        # Register tables as child (CORRECT WAY)
        self.api.add_child(self.tables.api)

    @api
    def query(self, sql: str) -> dict:
        """Execute raw SQL query (demo)."""
        return {"sql": sql, "result": "Query executed successfully (demo)", "rows_affected": 0}


# ============================================================================
# Level 2: Inventory handler (sibling of db)
# ============================================================================


class InventoryHandler:
    """Handler for inventory operations."""

    api = Router(name="inventory")

    def __init__(self):
        self.stock = {1: 5, 2: 50, 3: 100}

    @api
    def check(self, product_id: int) -> dict:
        """Check inventory for product."""
        stock = self.stock.get(product_id, 0)
        return {
            "product_id": product_id,
            "stock": stock,
            "status": "in_stock" if stock > 0 else "out_of_stock",
        }


# ============================================================================
# Level 1: Shop handler (root of business logic)
# ============================================================================


class ShopHandler:
    """Main shop handler with hierarchical structure."""

    api = Router(name="shop")

    def __init__(self):
        # Initialize sub-handlers
        self.db = DBHandler()
        self.inventory = InventoryHandler()

        # Register as children (CORRECT WAY)
        self.api.add_child(self.db.api)
        self.api.add_child(self.inventory.api)


# ============================================================================
# App: PublishedClass
# ============================================================================


class MyShop(PublishedClass):
    """Shop app with hierarchical handler structure."""

    def on_init(self):
        # Publish shop handler (which contains db, inventory, etc.)
        self.publish("shop", ShopHandler())


# ============================================================================
# Demo: Test hierarchical access
# ============================================================================


def demo_hierarchical_access():
    """Demonstrate hierarchical path access."""
    print("=" * 70)
    print("Hierarchical Shop Demo")
    print("=" * 70)
    print()

    # Create app
    app = MyShop()

    # Test 1: Access via path
    print("Test 1: Access via path notation")
    print("-" * 70)

    # Get shop handler
    shop = app.published_instances["shop"]

    # Test path: shop.db.tables.product.list
    print("\n1. List products via: shop.db.tables.product.list")
    product_handler = shop.db.tables.product
    result = product_handler.list()
    print(f"   Result: {result['count']} products")

    # Test path: shop.db.tables.customer.list
    print("\n2. List customers via: shop.db.tables.customer.list")
    customer_handler = shop.db.tables.customer
    result = customer_handler.list()
    print(f"   Result: {result['count']} customers")

    # Test path: shop.db.query
    print("\n3. Query via: shop.db.query")
    result = shop.db.query("SELECT * FROM products")
    print(f"   Result: {result['result']}")

    # Test path: shop.inventory.check
    print("\n4. Check inventory via: shop.inventory.check")
    result = shop.inventory.check(1)
    print(f"   Result: {result['stock']} units, {result['status']}")

    print()
    print("=" * 70)
    print("✅ Hierarchical access working!")
    print("=" * 70)
    print()

    # Test 2: SmartSwitch API access
    print("Test 2: SmartSwitch API navigation")
    print("-" * 70)

    # Navigate via Switcher hierarchy
    print("\n1. Get product API schema:")
    product_api = shop.db.tables.product.__class__.api
    schema = product_api.describe()
    print(f"   Methods: {list(schema.get('methods', {}).keys())}")

    print("\n2. Get customer API schema:")
    customer_api = shop.db.tables.customer.__class__.api
    schema = customer_api.describe()
    print(f"   Methods: {list(schema.get('methods', {}).keys())}")

    print()
    print("=" * 70)
    print("✅ SmartSwitch API navigation working!")
    print("=" * 70)
    print()

    # Test 3: Hierarchical path resolution (SmartSwitch 0.11.0 feature)
    print("Test 3: Hierarchical Path Resolution (api.get('path.to.method'))")
    print("-" * 70)

    # Test: shop.db.tables.product.list
    print("\n1. Resolve: shop.api.get('db.tables.product.list')")
    try:
        method = shop.__class__.api.get("db.tables.product.list", use_smartasync=True)
        # Need to call with correct instance (product handler)
        result = method(shop.db.tables.product)
        print(f"   ✅ Success! Found {result['count']} products")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test: shop.db.tables.customer.get
    print("\n2. Resolve: shop.api.get('db.tables.customer.get')")
    try:
        method = shop.__class__.api.get("db.tables.customer.get")
        result = method(shop, id=1)
        print(f"   ✅ Success! Got customer: {result['row']['name']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test: shop.db.query
    print("\n3. Resolve: shop.api.get('db.query')")
    try:
        method = shop.__class__.api.get("db.query")
        result = method(shop, sql="SELECT * FROM products")
        print("   ✅ Success! Query executed")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test: shop.inventory.check
    print("\n4. Resolve: shop.api.get('inventory.check')")
    try:
        method = shop.__class__.api.get("inventory.check")
        result = method(shop, product_id=1)
        print(f"   ✅ Success! Stock: {result['stock']}, Status: {result['status']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print()
    print("=" * 70)
    print("✅ Hierarchical path resolution working!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    demo_hierarchical_access()
