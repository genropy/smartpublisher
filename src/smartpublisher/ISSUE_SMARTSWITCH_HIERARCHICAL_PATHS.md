# SmartSwitch Feature Request: Hierarchical Path Support

## Summary

SmartSwitch should support accessing nested Switcher hierarchies using dot notation:

```python
api.get('parent.child.grandchild.method')
```

## Use Case

Building hierarchical APIs with nested handlers:

```python
# Structure
shop/
  ├─ db/
  │   ├─ tables/
  │   │   ├─ product/
  │   │   │   ├─ list()
  │   │   │   └─ get(id)
  │   │   └─ customer/
  │   │       └─ list()
  │   └─ query(sql)
  └─ inventory/
      └─ check(product_id)

# CLI usage
$ smpub myshop shop db tables product list
$ smpub myshop shop db tables customer get --id 1
$ smpub myshop shop inventory check --product_id 123

# Internal resolution
method = api.get('shop.db.tables.product.list')
result = method(instance)
```

## Current Behavior

```python
shop_api = Switcher(name="shop")
db_api = Switcher(name="db")
db_api.parent = shop_api

# This FAILS:
method = shop_api.get('db.tables.product.list')
# Error: "No child switch named 'db'"
```

SmartSwitch doesn't automatically navigate through nested Switchers using dot notation.

## Desired Behavior

```python
# Should work:
method = shop_api.get('db.tables.product.list')

# Should also work:
method = shop_api.get('db.query')  # Direct child
method = shop_api.get('inventory.check')  # Another branch
```

## Implementation Suggestion

When `Switcher.get(name)` receives a name with dots:

1. Split by '.' → `['db', 'tables', 'product', 'list']`
2. Navigate through hierarchy:
   - Get child 'db' → `db_switcher`
   - Get child 'tables' from `db_switcher` → `tables_switcher`
   - Get child 'product' from `tables_switcher` → `product_switcher`
   - Get method 'list' from `product_switcher` → `list_method`
3. Return the final callable

## Benefits

1. **Clean CLI routing**: Parse `args` and resolve directly via SmartSwitch
2. **No manual navigation**: Framework doesn't need to walk the tree manually
3. **Consistent with SmartSwitch philosophy**: "Single source of truth"
4. **Simpler completion**: Can use `describe()` at any level
5. **Natural hierarchy**: Matches URL routing patterns (`/shop/db/tables/product/list`)

## Related Files

- `smartpublisher/example_shop_hierarchical.py` - Demo of desired structure
- `smartpublisher/cli.py` - CLI that needs hierarchical routing

## Current Workaround

Manual navigation through object attributes:

```python
# Instead of: api.get('db.tables.product.list')
# Must do:
obj = instance.db.tables.product
method = obj.__class__.api.get('list')
```

This breaks SmartSwitch as "single source of truth" principle.

## Priority

**High** - Essential for building realistic hierarchical applications with smartpublisher.

---

**Context**: Building smartpublisher framework that uses SmartSwitch for CLI/API dispatch. Hierarchical structures are common in real applications (REST APIs, CLI tools, etc.).
