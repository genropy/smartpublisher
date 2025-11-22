# Publisher Reference

This document tracks the authoritative behavior for the `Publisher` subsystem and
the `smpub` CLI. Treat it as the source of truth when evolving code or docs.

## CLI Expectations (`smpub --help`)

Running `smpub --help` must expose everything users can do via CLI. Today the CLI
inspects `publisher.api` and therefore must surface at least the root commands
and handler commands described below.

### Root commands (prefixed with `/`)

| Command | Description |
| --- | --- |
| `/serve [channel=http] [**options]` | Stub for activating a channel. Currently returns a disabled message but must remain visible in help. |
| `/quit` | Stub for shutdown command. Returns a disabled message but must be documented. |
| `/add <name> <path/to/module.py[:ClassName]> [app_args...] [--kw value...]` | Publishes a new application. The class defaults to `Main` if omitted. Extra positional and keyword arguments are forwarded to the app constructor. |
| `/remove <name>` | Unregisters a previously published app. |
| `/list` | Lists registered apps and their metadata (`path`, `module`, `class`). |
| `/getapp <name>` | Returns metadata for a specific app. |
| `/unload_app <name>` | Wrapper around `/remove` for compatibility; returns status payload. |
| `/savestate [path]` | Serializes the current registry to a JSON snapshot (default `~/.smartlibs/publisher/state.json`). |
| `/loadstate [path] [skip_missing=false]` | Rebuilds the registry from a snapshot by re-invoking `/add` for each entry. Supports skipping missing specs when `skip_missing` is true. |
| `/autosave [true|false]` | Reads or sets autosave. When enabled (default), every mutation calls `/savestate` to the configured path. |

**Naming rules**
- App names must be unique.
- App names cannot start with `/` (reserved for root commands).
- Names like `serve` or `quit` are allowed because root commands always include the slash.

### Handler and system commands

Every published app (a handler) exposes its own SmartRoute API via `handler.api`.
The CLI should allow:
- `smpub <handler>` to show handler-specific help.
- `smpub <handler> <method> [args...]` to execute handler methods (SmartRoute performs validation).
- `smpub _system list_handlers` and other system commands for introspection (`SystemCommands` handler).

### Argument parsing for `/add`

The CLI must split tokens after `/add` so that positional arguments are passed
as `*args` and options in the form `--key value` or `--key=value` become
`**kwargs`. `--` terminates option parsing and forces the rest into positional
arguments. This logic currently lives in `CLIChannel._split_cli_args`.

## Application loading model

`Publisher.add` delegates to `AppManager` which:
1. Parses the spec `<path/to/module.py[:ClassName]>`.
2. Resolves the filesystem path **to a single file** (no directories/packages).
3. Loads that file with `SourceFileLoader` (no `sys.path` mutation), retrieves the class (default `Main`), and instantiates it
   with the forwarded arguments.
4. Stores metadata plus the original `spec/args/kwargs` in `publisher._state` for persistence via `/savestate`.

**Implications**
- Relative imports inside the app module may fail because there is no package context; only code in that file is guaranteed to load.
- State snapshots must be kept in sync with the actual files on disk; `/loadstate` will fail if a spec path no longer exists (unless `skip_missing=true`).

## Future Channels (FastAPI focus)

We plan to expose Publisher functionality over HTTP using FastAPI. There are two
possible integration models:

1. **Per-app FastAPI server**: each published app runs its own FastAPI application
   on its own event loop/port. Publisher acts mainly as a registry, and `/serve`
   could eventually spin up a channel that proxies requests to the appropriate app.

2. **Shared Publisher FastAPI**: Publisher owns a single FastAPI application and
   exposes each handler under different URL prefixes. Apps would not create their
   own loops; instead they plug their HTTP handlers into the Publisher’s router.
   This allows a single port, centralized auth/middleware, and easier management.

The long-term direction is to make Publisher capable of running FastAPI itself,
so apps can optionally join the shared loop while still leaving room for custom
deployments (separate loops) if needed. Decisions taken here must be mirrored in
the root commands and their help text.

## Enforcement

- Whenever CLI functionality changes, update both this document and the module
  docstring in `src/smartpublisher/publisher.py`.
- If `/serve` or `/quit` gain real implementations, document parameters, side
  effects, and how they interact with channel instances.
- Additional channels (HTTP/FastAPI) must describe whether they reuse the
  Publisher loop or spawn independent servers, and how users activate them.
