# Interactive Mode

User-friendly parameter prompting with questionary.

## Installation

```bash
# 1. Install questionary
pip install questionary

# 2. Install smpub
pip install smpub
```

## Complete Test Sequence

### Step 1: Install and Setup

```bash
# From smpub project root
cd /path/to/smpub

# Install in development mode
pip install -e .

# Verify smpub command is available
which smpub
```

### Step 2: Register Test App

```bash
# Register the mail service example app
smpub add mailapp --path ./examples/mail_app

# Verify registration
smpub list
```

### Step 3: Test Interactive Mode

```bash
# Test 1: Add mail account with interactive prompts
smpub mailapp account add --interactive
# Questionary will show prompts:
# ? name (str): [Enter account identifier]
# ? smtp_host (str): [Enter SMTP hostname]
# ? smtp_port (int) [587]: [Port number or press Enter for default]
# ? username (str): [Email address]
# ? use_tls (bool) (Y/n): [Yes/No confirmation]
# ? auth_method: [Arrow keys to select: plain/login/oauth2]

# Test 2: Send email with all parameters
smpub mailapp mail send --interactive
# Questionary prompts in sequence:
# ? account (str): [Account name to use]
# ? to (str): [Recipient email]
# ? subject (str): [Email subject]
# ? body (str): [Message body]
# ? priority: [Select low/normal/high with arrow keys]
# ? html (bool) (y/N): [Yes/No confirmation]

# Test 3: Send email using short form flag
smpub mailapp mail send -i
# Same prompts as Test 2

# Test 4: List accounts (no parameters, no interactive needed)
smpub mailapp account list
```

### Step 4: Verify Results

```bash
# List sent messages
smpub mailapp mail list

# Clear messages
smpub mailapp mail clear

# Delete an account
smpub mailapp account delete work
```

### Step 5: Cleanup

```bash
# Remove from registry
smpub remove mailapp

# Verify removal
smpub list
```

## What Happens

1. **`--interactive` flag** triggers questionary prompts
2. **For each parameter**:
   - String/Int/Float: Text input with default value shown
   - Boolean: Yes/No confirmation (Y/n or y/N based on default)
   - Literal: Arrow-key menu selection with allowed values
   - Default values shown in brackets or as default selection
3. **Questionary UI features**:
   - Clean, modern terminal interface
   - **Tab**: Navigate forward to next field
   - **Shift+Tab**: Navigate backward to previous field
   - Arrow keys to navigate menu selections
   - Enter to submit form, Ctrl+C to cancel
   - Built-in validation support
4. **Validation** happens after all inputs collected via Pydantic
5. **Method executes** with validated parameters

## Interactive vs Normal Mode

```bash
# Normal mode: all arguments on command line
smpub mailapp mail send work "user@example.com" "Subject" "Body text" normal false

# Interactive mode: questionary prompts for each parameter
smpub mailapp mail send --interactive
```

## Questionary Advantages

- **Pure Python**: No external CLI tools required
- **Modern UI**: Clean, intuitive interface with colors
- **Rich features**: Validation, autocompletion, smart defaults
- **Cross-platform**: Works on Windows, macOS, Linux
- **Active development**: Well-maintained with good documentation
- **Better UX**: More user-friendly than traditional TUI tools

## Parameter Types

### Text Input (str, int, float)

```text
? name (str): Alice
? age (int) [25]: 30
? price (float) [9.99]: 12.50
```

### Boolean Confirmation

```text
? enabled (bool) (Y/n): y
? debug (bool) (y/N): n
```

Default shown as uppercase (Y vs y, N vs n).

### Literal Selection

```text
? priority:
  ❯ low
    normal
    high
```

Use arrow keys to select, Enter to confirm.

See [CLI Mode](cli-mode.md) for more examples.
