# Calculator Example

Complete calculator application demonstrating smpub features.

## Source Code

See [examples/calculator_http.py](https://github.com/genropy/smartpublisher/blob/main/examples/calculator_http.py)

## Features

- Multiple arithmetic operations
- CLI and HTTP modes
- Pydantic validation
- History tracking

## CLI Usage

```bash
python calculator_http.py calc add 10 20
python calculator_http.py calc multiply 3.5 2.0
python calculator_http.py calc history
```

## HTTP Usage

```bash
# Start server
python calculator_http.py

# Use API
curl -X POST http://localhost:8000/calc/add \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 20}'
```

Visit http://localhost:8000/docs for Swagger UI.
