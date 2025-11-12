#!/usr/bin/env python3
"""Populate the published_shop database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.sample_shop.shop import Shop

db_path = Path(__file__).parent / "shop.db"
shop = Shop(f"sqlite:{db_path}")
result = shop.populateDb()
print(f"Database populated: {result}")
