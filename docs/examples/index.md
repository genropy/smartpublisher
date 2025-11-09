# Examples

## Available Examples

### Calculator App

A complete calculator application demonstrating:
- Basic arithmetic operations
- CLI and HTTP modes
- Parameter validation
- History tracking

See [calculator_http.py](https://github.com/genropy/smpub/blob/main/examples/calculator_http.py)

[Read more](calculator.md)

## Running Examples

Clone the repository:

```bash
git clone https://github.com/genropy/smpub.git
cd smpub/examples
```

Install dependencies:

```bash
pip install -e ..[http]
```

Run examples:

```bash
# CLI mode
python calculator_http.py calc add 10 20

# HTTP mode
python calculator_http.py
# Visit http://localhost:8000/docs
```
