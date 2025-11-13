"""
smartpublisher Publisher for Shop class.

This is ONLY the publisher - the actual Shop implementation is in sample_shop/.

Key points:
1. Shop is a standalone Python library (see ../sample_shop/)
2. This file just imports Shop and publishes it
3. smartpublisher is a thin layer - Shop doesn't know about it

To use Shop without smartpublisher, see:
- ../sample_shop/example_pythonic.py
- ../sample_shop/shop_usage.ipynb
"""

import sys
from pathlib import Path

# Add smpub root to path (to import smartpublisher package)
# And add examples parent to path (to import examples.demo_shop)
smpub_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(smpub_root))

from smartpublisher import Publisher  # noqa: E402
from examples.demo_shop.sample_shop.shop import Shop  # noqa: E402


class PublishedShop(Publisher):
    """
    Publisher for Shop class.

    Notice how simple this is:
    1. Import Shop from sample_shop (standalone library)
    2. Instantiate it (normal Python object)
    3. Publish it (add CLI/HTTP layer)

    That's it! smartpublisher is just a thin publishing layer.

    Note: We implement on_init() instead of __init__() to avoid calling super().
    Publisher.__init__() will call our on_init() after setting up the infrastructure.

    The CLI command remains 'smpub' for convenience:
        python main.py types list
    """

    def on_init(self):
        """Initialize and publish Shop components."""
        # Import and instantiate Shop - it's just a normal Python class
        # Use a database file in the current directory
        db_path = Path(__file__).parent / "shop.db"
        shop = Shop(f"sqlite:{db_path}")

        # Publish table managers for CLI/HTTP access
        # Note: Table classes use 'dbop' instead of 'api' for their Switcher
        self.publish("types", shop.db.table("types"), switcher_name="dbop")
        self.publish("articles", shop.db.table("articles"), switcher_name="dbop")
        self.publish("purchases", shop.db.table("purchases"), switcher_name="dbop")


if __name__ == "__main__":
    app = PublishedShop()
    app.run()
