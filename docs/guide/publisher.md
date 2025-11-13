# Publisher Class

The Publisher class is the base for all smpub applications.

## Basic Usage

```python
from smartpublisher import Publisher

class MyApp(Publisher):
    def initialize(self):
        # Register your handlers here
        pass

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

## Methods

### publish()

Register a handler for CLI/API exposure.

### run()

Run the application in CLI or HTTP mode.

See [API Reference](../api/publisher.md) for complete documentation.
