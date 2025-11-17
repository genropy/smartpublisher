# Bash Completion for smpub

This directory contains the bash completion script for the `smpub` command.

## Features

- Tab completion for system commands (`.apps`, etc.)
- Tab completion for registered app names
- Tab completion for handler names within apps
- Tab completion for methods within handlers
- **Powered by SmartSwitch** - suggestions come directly from `Switcher.describe()`

## Installation

### Option 1: User-level installation (recommended)

```bash
# Create directory
mkdir -p ~/.bash_completion.d

# Copy script
cp bash_completion/smpub ~/.bash_completion.d/

# Add to .bashrc
echo 'source ~/.bash_completion.d/smpub' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

### Option 2: System-wide installation (requires sudo)

```bash
# Copy to system directory
sudo cp bash_completion/smpub /etc/bash_completion.d/

# Reload shell
source /etc/bash_completion.d/smpub
```

### Option 3: One-line install

```bash
# From the smartpublisher directory
bash -c 'mkdir -p ~/.bash_completion.d && cp bash_completion/smpub ~/.bash_completion.d/ && echo "source ~/.bash_completion.d/smpub" >> ~/.bashrc && echo "✓ Installed! Run: source ~/.bashrc"'
```

## Usage Examples

Once installed, use Tab to get suggestions:

```bash
# First level: system commands + app names
$ smpub <TAB>
.apps    myapp    otherapp

# System command methods
$ smpub .apps <TAB>
add    list    remove    getapp

# App handlers
$ smpub myapp <TAB>
shop    users    _system

# Handler methods
$ smpub myapp shop <TAB>
list    create    update    delete
```

## How It Works

The bash completion script calls `smpub --complete <level> <args...>` to get suggestions:

1. **Level 0** (after `smpub`): Returns system commands + registered app names
2. **Level 1** (after `smpub .apps`): Returns registry methods from `AppRegistry.api.describe()`
3. **Level 1** (after `smpub myapp`): Returns handler names from `app.published_instances`
4. **Level 2** (after `smpub myapp shop`): Returns methods from `handler.api.describe()`

All suggestions come from **SmartSwitch** via `describe()` - zero duplication!

## Troubleshooting

### Completion not working

1. Verify installation:
   ```bash
   type _smpub_completion
   # Should show: _smpub_completion is a function
   ```

2. Test manually:
   ```bash
   smpub --complete 0
   # Should show: .apps myapp otherapp (or similar)
   ```

3. Reload shell:
   ```bash
   source ~/.bashrc
   ```

### No suggestions appearing

- Make sure `smpub` is in your PATH
- Try completing a registered app: `smpub .apps list` first to see available apps

## Uninstallation

```bash
# Remove script
rm ~/.bash_completion.d/smpub

# Remove from .bashrc
sed -i '/smpub/d' ~/.bashrc

# Reload shell
source ~/.bashrc
```

## Notes

- Completion is dynamic - it queries the registry and SmartSwitch API in real-time
- Suggestions update automatically when you register/unregister apps
- The script is fast because it only loads what's needed for completion
