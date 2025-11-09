# Validation

Pydantic-based parameter validation.

## Automatic Validation

Type hints are automatically validated:

```python
@api
def my_method(self, count: int, name: str):
    # count is validated as int
    # name is validated as str
    pass
```

See [Architecture](../appendix/architecture.md) for validation flow.
