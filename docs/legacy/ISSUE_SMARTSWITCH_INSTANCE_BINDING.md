# SmartSwitch Feature Request: Instance Binding for Hierarchical Paths

## Summary

When using `add_child(instance)` to build hierarchical Switcher structures, SmartSwitch should **automatically bind methods to their correct instances** when resolving hierarchical paths.

## Current Behavior

```python
from smartswitch import Switcher

class ProductHandler:
    api = Switcher(name='product')

    def __init__(self):
        self.items = ['laptop', 'mouse']

    @api
    def list(self):
        return {'items': self.items}

class ShopHandler:
    api = Switcher(name='shop')

    def __init__(self):
        self.product = ProductHandler()
        self.api.add_child(self.product)  # Pass instance

shop = ShopHandler()

# Resolve hierarchical path
method = shop.api.get('product.list')

# ❌ FAILS - method not bound to instance
result = method()  # TypeError: missing 1 required positional argument: 'self'

# ✅ WORKAROUND - must manually navigate to instance
result = method(shop.product)  # Works, but manual
```

## Desired Behavior

```python
shop = ShopHandler()

# Resolve hierarchical path
method = shop.api.get('product.list')

# ✅ Should work - method automatically bound to correct instance
result = method()  # Should return {'items': ['laptop', 'mouse']}
```

## Problem

When you call `add_child(instance)`:
1. SmartSwitch **discovers** the Switcher from the instance (`instance.api`)
2. SmartSwitch **links** the child Switcher to parent Switcher
3. **BUT**: SmartSwitch **does not store** the instance reference

Later, when you resolve a path like `shop.api.get('product.list')`:
1. SmartSwitch **finds** the method correctly ✅
2. But returns an **unbound** method ❌
3. You must **manually navigate** to the instance: `method(shop.product)` ❌

## Use Case: CLI with Deep Hierarchies

```python
# CLI command: $ myapp shop db tables product list
# Path: 'shop.db.tables.product.list'

# Current: Must manually navigate instances
handler = app.published_instances['shop']
instance = handler.db.tables.product  # Manual navigation ❌
method = handler.api.get('db.tables.product.list')
result = method(instance)

# Desired: Automatic binding
handler = app.published_instances['shop']
method = handler.api.get('db.tables.product.list')
result = method()  # Already bound to correct instance ✅
```

## Proposed Solution

When `add_child()` receives an **instance** (not a bare Switcher), store the binding:

```python
class Switcher:
    def __init__(self, ...):
        self._child_instances = {}  # New: map child_name → instance

    def add_child(self, child: Any, name: Optional[str] = None):
        if isinstance(child, Switcher):
            # Bare Switcher - no instance binding
            self._attach_child_switcher(child, explicit_name=name)
        else:
            # Instance with Switcher - discover AND bind
            for attr_name, switch in self._iter_unbound_switchers(child):
                derived_name = switch.name or attr_name
                self._attach_child_switcher(switch, explicit_name=derived_name)
                # NEW: Store instance binding
                self._child_instances[derived_name] = child

    def get(self, selector: str, ...):
        node, method_name = self._resolve_path(selector)
        method = node._methods[method_name].func

        # NEW: If we have an instance binding, return bound method
        if selector in self._child_instances:
            instance = self._child_instances[selector]
            return method.__get__(instance, type(instance))

        # Otherwise, return unbound method (current behavior)
        return method
```

## Alternative: Instance-Aware Path Resolution

Instead of modifying `get()`, provide a new method that takes the root instance:

```python
class Switcher:
    def get_bound(self, selector: str, root_instance):
        """
        Resolve path and return method bound to correct instance.

        Args:
            selector: Dotted path like 'db.tables.product.list'
            root_instance: Root instance to navigate from

        Returns:
            Bound method ready to call
        """
        # Navigate through instances following the path
        path_parts = selector.split('.')
        instance = root_instance
        for part in path_parts[:-1]:
            instance = getattr(instance, part)

        # Get method from Switcher
        node, method_name = self._resolve_path(selector)
        method = node._methods[method_name].func

        # Bind to final instance
        return method.__get__(instance, type(instance))

# Usage
shop = ShopHandler()
method = shop.api.get_bound('product.list', shop)
result = method()  # ✅ Bound to shop.product
```

## Benefits

1. **Simpler CLI routing**: No manual instance navigation
2. **Natural API**: Hierarchical paths resolve to callable methods
3. **Consistent with expectation**: If you can resolve the path, you should be able to call it
4. **Enables deep hierarchies**: Makes complex structures practical

## Backward Compatibility

Both solutions are **fully backward compatible**:

**Solution 1** (auto-binding):
- Only affects behavior when `add_child()` receives an instance
- Bare Switcher children remain unchanged
- Existing code continues to work

**Solution 2** (new method):
- Adds new `get_bound()` method
- Existing `get()` unchanged
- Opt-in feature

## Related

- Issue #31 - Hierarchical path support (✅ already implemented)
- This issue - Instance binding for hierarchical paths (requested)

## Priority

**High** - Essential for practical use of hierarchical Switcher structures in frameworks like smartpublisher.

---

**Context**: smartpublisher needs to route CLI commands like `$ smpub myapp shop db tables product list` to deeply nested handler methods. SmartSwitch correctly resolves the path, but we must manually navigate through instances.
