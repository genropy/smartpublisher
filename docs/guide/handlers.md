# Handler Classes

Handlers contain your business logic.

## Basic Handler

```python
from smartpublisher import PublishedClass
from smartswitch import Switcher

class MyHandler(PublishedClass):
    __slots__ = ('data',)
    api = Switcher(prefix='my_')
    
    def __init__(self):
        self.data = {}
    
    @api
    def my_method(self, param: str) -> str:
        """Process something."""
        return f"Processed: {param}"
```

See [Publishing Guide](../user-guide/publishing-guide.md) for complete examples.
