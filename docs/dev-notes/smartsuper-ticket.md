# Ticket: Investigate smartsuper usage in Publisher

## Summary
Using `@smartsuper` on `Publisher.__init__` causes the superclass constructor (`PublishedClass.__init__`) to be invoked automatically **before** the body of `Publisher.__init__`. The decorator logic also auto-wraps all overridden methods in the class hierarchy. In our case this leads to duplicated initialization of the root router and, consequently, to multiple `_system` handlers being registered.

## Observed Behavior
- When `Publisher` inherited from `PublishedClass` with `@smartsuper` applied to `__init__`, every instantiation triggered:
  1. `PublishedClass.__init__` (via `smartsuper`),
  2. our explicit initialization logic (registries, channel registry, handlers),
  3. implicit re-binding of routers and children.
- The system command `_system` was added twice to the router tree, provoking `ValueError: Child name collision: _system`.
- Subsequent `publish()` calls also produced `TypeError: Pass an object instance, not the Router descriptor` because the decorator changed the order in which routers were bound.

## Impact
- CLI initialization failed before any command execution.
- Unit tests `TestPublisher.test_init_default` and others crashed consistently.
- Debugging became harder because the decorator hides the actual control flow—`super().__init__()` happens implicitly and its side effects are executed twice.

## Proposed Actions
1. Remove `@smartsuper` from `Publisher` (already done in current branch) and rely on an explicit `super().__init__()` call to make the constructor intent clear.
2. Document in `docs/dev-notes` that `smartsuper` should be used only in classes where double initialization of routers is harmless.
3. (Optional) consider linting/CI rule to forbid `@smartsuper` on classes inheriting from `PublishedClass`.

## References
- File: `src/smartpublisher/publisher.py`
- Related tests: `tests/test_publisher.py::TestPublisher::test_init_default` and `tests/test_publisher.py::TestPublisher::test_load_app_success`
