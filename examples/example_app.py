"""
Example application demonstrating the new architecture.

This shows:
1. Business logic in handlers (channel-agnostic)
2. Publisher publishing handlers
3. CLI channel with utility commands
4. HTTP channel with utility commands
5. Two-level command structure
"""

from smartroute.core import Router

# Try relative imports first (when used as package)
# Fall back to absolute imports (when run directly)
try:
    from .published import PublishedClass
    from .channels.cli import PublisherCLI
    from .channels.http import PublisherHTTP
except ImportError:
    from published import PublishedClass
    from channels.cli import PublisherCLI
    from channels.http import PublisherHTTP


# ============================================================================
# BUSINESS LOGIC - Channel Agnostic
# ============================================================================


class ShopHandler:
    """
    Shop handler - business logic only.

    NO print statements, NO transport code.
    Just pure business logic returning structured data.
    """

    api = Router(name="shop")

    def __init__(self):
        """Initialize with sample data."""
        self.products = [
            {"id": 1, "name": "Laptop Pro", "price": 1299.99, "stock": 5},
            {"id": 2, "name": "Wireless Mouse", "price": 29.99, "stock": 50},
            {"id": 3, "name": "USB-C Cable", "price": 12.99, "stock": 100},
        ]

    @api
    def list(self) -> dict:
        """
        List all products.

        Returns structured data - NO print!
        """
        return {"total": len(self.products), "products": self.products}

    @api
    def get(self, product_id: int) -> dict:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            dict: Product data or error
        """
        for product in self.products:
            if product["id"] == product_id:
                return {"product": product}

        return {"error": f"Product {product_id} not found"}

    @api
    def search(self, query: str) -> dict:
        """
        Search products by name.

        Args:
            query: Search query

        Returns:
            dict: Matching products
        """
        matches = [p for p in self.products if query.lower() in p["name"].lower()]

        return {"query": query, "matches": len(matches), "products": matches}

    @api
    def update_stock(self, product_id: int, quantity: int) -> dict:
        """
        Update product stock.

        Args:
            product_id: Product ID
            quantity: New quantity

        Returns:
            dict: Update result
        """
        for product in self.products:
            if product["id"] == product_id:
                old_stock = product["stock"]
                product["stock"] = quantity
                return {
                    "status": "updated",
                    "product_id": product_id,
                    "old_stock": old_stock,
                    "new_stock": quantity,
                }

        return {"error": f"Product {product_id} not found"}


# ============================================================================
# APP - Inherits from PublishedClass
# ============================================================================


class ShopApp(PublishedClass):
    """
    Shop application - business logic only.

    Inherits from PublishedClass to get root Switcher and publish() method.
    """

    def on_init(self):
        """Initialize and publish handlers."""
        # Create and publish shop handler
        shop = ShopHandler()
        self.publish("shop", shop)

    def smpub_on_add(self):
        """Custom welcome message."""
        return {
            "message": "ShopApp registered successfully!",
            "description": "A simple product management system",
            "quick_start": [
                "# List products:",
                "smpub run shopapp shop list",
                "",
                "# Search products:",
                "smpub run shopapp shop search --query laptop",
                "",
                "# Start HTTP server:",
                "smpub serve shopapp",
                "",
                "# Then visit:",
                "http://localhost:8000/docs  (Swagger UI)",
                "http://localhost:8000/_http/health  (Health check)",
            ],
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================


def example_cli():
    """Example: CLI usage."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: CLI Channel")
    print("=" * 70 + "\n")

    # Create app
    app = ShopApp()

    # Create CLI channel
    cli = PublisherCLI(app)

    print("1. List products:")
    print("   $ smpub run shopapp shop list")
    cli.run(["shop", "list"])

    print("\n2. Get product by ID:")
    print("   $ smpub run shopapp shop get --product_id 1")
    # Note: In real implementation, this would parse --product_id
    # For skeleton, we show the concept

    print("\n3. CLI utility command - help:")
    print("   $ smpub run shopapp cli help")
    cli.run(["cli", "help"])

    print("\n4. CLI utility command - version:")
    print("   $ smpub run shopapp cli version")
    cli.run(["cli", "version"])


def example_http():
    """Example: HTTP usage."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: HTTP Channel")
    print("=" * 70 + "\n")

    # Create app
    app = ShopApp()

    # Create HTTP channel
    http = PublisherHTTP(app)

    print("HTTP channel provides:")
    print("\n1. Business endpoints (from publisher.api):")
    print("   - GET /shop/list")
    print("   - GET /shop/get?product_id=1")
    print("   - GET /shop/search?query=laptop")
    print("   - POST /shop/update_stock")

    print("\n2. HTTP utility endpoints (from http.http_api):")
    print("   - GET /_http/health")
    print("   - GET /_http/openapi")
    print("   - GET /_http/metrics")

    print("\n3. Auto-generated docs:")
    print("   - http://localhost:8000/docs (Swagger UI)")
    print("   - http://localhost:8000/redoc (ReDoc)")

    print("\nTest HTTP utility commands:")
    print("\n- Health check:")
    health = http.http_api["health"]()
    print(f"  {health}")

    print("\n- Metrics:")
    metrics = http.http_api["metrics"]()
    print(f"  {metrics}")

    print("\nTo start server:")
    print("  http.run(port=8000)")


def example_two_level_commands():
    """Example: Two-level command structure."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Two-Level Command Structure")
    print("=" * 70 + "\n")

    app = ShopApp()

    print("LEVEL 1: Business Commands (channel-agnostic)")
    print("-" * 50)
    print("These are defined in handlers and work on ALL channels:\n")

    print("Handler: ShopHandler")
    print("  Methods in shop.api:")
    shop_api = app.published_instances["shop"].__class__.api
    for method_name in shop_api.entries():
        print(f"    - {method_name}()")

    print("\nAvailable on:")
    print("  - CLI:  smpub run shopapp shop list")
    print("  - HTTP: GET /shop/list")
    print("  - SOAP: <future>")
    print('  - WS:   {"handler": "shop", "method": "list"}')

    print("\n\nLEVEL 2: Channel Commands (transport-specific)")
    print("-" * 50)

    print("\nCLI Channel (cli.cli_api):")
    cli = PublisherCLI(app)
    for method_name in cli.cli_api.entries():
        print(f"  - {method_name}()")
    print("  Usage: smpub run shopapp cli help")

    print("\nHTTP Channel (http.http_api):")
    http = PublisherHTTP(app)
    for method_name in http.http_api.entries():
        print(f"  - {method_name}()")
    print("  Usage: GET /_http/health")


def example_single_source_of_truth():
    """Example: Single source of truth via Switcher."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Single Source of Truth")
    print("=" * 70 + "\n")

    app = ShopApp()

    print("All commands are in Switcher → Auto-generated everything:")
    print("-" * 50)

    print("\n1. Auto-generated CLI help:")
    api_schema = app.api.describe()
    print(f"   Methods: {list(api_schema.get('methods', {}).keys())}")

    print("\n2. Auto-generated OpenAPI:")
    http = PublisherHTTP(app)
    openapi_spec = http.http_api["openapi_schema"]()
    print(f"   Paths: {list(openapi_spec.get('paths', {}).keys())}")

    print("\n3. Auto-generated system info:")
    system_info = app.api["_system"].list_handlers()
    print(f"   Handlers: {list(system_info['handlers'].keys())}")

    print("\nNO MANUAL DUPLICATION!")
    print("- Help comes from Switcher.describe()")
    print("- OpenAPI comes from Switcher.describe()")
    print("- WSDL (future) comes from Switcher.describe()")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SmartPublisher - New Architecture Examples")
    print("=" * 70)

    # Run examples
    example_cli()
    example_http()
    example_two_level_commands()
    example_single_source_of_truth()

    print("\n" + "=" * 70)
    print("Key Takeaways")
    print("=" * 70)
    print(
        """
1. Publisher is MINIMAL (~80 lines) - orchestration only
2. Business logic in handlers - NO print, NO transport code
3. Each channel is separate class with own Switcher
4. Two-level commands:
   - Business: publisher.api (works everywhere)
   - Channel: channel.xxx_api (transport-specific)
5. Single source of truth: Switcher for introspection
6. Easy to extend: Add SOAP/WebSocket/gRPC channels
"""
    )
