# Handler Classes

Handlers contain your business logic.

## Basic Handler

```python
from smartpublisher import PublishedClass
from smartroute import Router, route

class MyHandler(PublishedClass):
    __slots__ = ('data',)
    api = Router(name='my')

    def __init__(self):
        self.data = {}

    @api
    def my_method(self, param: str) -> str:
        """Process something."""
        return f"Processed: {param}"
```

See [Publishing Guide](../user-guide/publishing-guide.md) for complete examples.
