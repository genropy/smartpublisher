# Quick Start

Get started with smpub in 5 minutes.

## Create a Simple Handler

Create a file `myapp.py`:

```python
from smpub import Publisher, PublishedClass
from smartswitch import Switcher

class GreetingHandler(PublishedClass):
    """Simple greeting handler."""

    __slots__ = ('greetings',)
    api = Switcher(prefix='greet_')

    def __init__(self):
        self.greetings = []

    @api
    def greet_hello(self, name: str) -> str:
        """Say hello to someone."""
        message = f"Hello, {name}!"
        self.greetings.append(message)
        return message

    @api
    def greet_goodbye(self, name: str) -> str:
        """Say goodbye to someone."""
        message = f"Goodbye, {name}!"
        self.greetings.append(message)
        return message

    @api
    def greet_history(self) -> list:
        """Show greeting history."""
        return self.greetings

class MyApp(Publisher):
    """My first smpub application."""

    def initialize(self):
        self.greeting = GreetingHandler()
        self.publish('greeting', self.greeting, cli=True, openapi=True)

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

## Try CLI Mode

Run commands:

```bash
# Say hello
python myapp.py greeting hello Alice
# Output: Hello, Alice!

# Say goodbye
python myapp.py greeting goodbye Bob
# Output: Goodbye, Bob!

# Show history
python myapp.py greeting history
# Output: ['Hello, Alice!', 'Goodbye, Bob!']
```

## Try Interactive Mode

Install dialog first:

```bash
# macOS
brew install dialog
```

Then use interactive mode:

```bash
python myapp.py greeting hello --interactive
# Prompts: name (str): _
```

## Try HTTP Mode

Install HTTP support:

```bash
pip install smpub[http]
```

Start the server:

```bash
# Run with no arguments = HTTP mode
python myapp.py
```

Open Swagger UI: http://localhost:8000/docs

Try the API:

```bash
curl -X POST http://localhost:8000/greeting/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'

# Response: {"status": "success", "result": "Hello, Alice!"}
```

## Next Steps

- [Publishing Guide](publishing-guide.md) - Learn how to expose your library
- [Handler Classes](../guide/handlers.md) - Deep dive into handlers
- [CLI Mode](../guide/cli-mode.md) - Advanced CLI features
- [HTTP Mode](../guide/http-mode.md) - Advanced HTTP features
