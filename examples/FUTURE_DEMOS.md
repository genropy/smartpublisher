# Future Demo Applications - Ideas

This document lists ideas for future demo applications to showcase smpub capabilities.

## Planned Demos

### 1. demo_shop ✅ (In Progress)
**Status**: Structure created, documentation in progress
**Focus**: SQL database, CRUD operations, table managers
**Shows**: Database adapters, SmartSwitch plugins, format negotiation

### 2. file_explorer
**Purpose**: File system navigation and operations
**Features**:
- Directory listing with filters
- File search (name, content, metadata)
- File operations (copy, move, delete)
- Permission management
- Archive creation/extraction

**Shows**: File I/O, path operations, async file handling

### 3. network_monitor
**Purpose**: Network services monitoring
**Features**:
- Service health checks
- Port scanning
- Ping monitoring
- HTTP endpoint monitoring
- Status dashboard

**Shows**: Async network operations, concurrent checks, status aggregation

### 4. genro_storage_demo
**Purpose**: Hybrid filesystem with genro-storage
**Features**:
- Multiple storage backends
- Unified API
- Metadata management
- Search and indexing

**Shows**: Adapter pattern, genro-storage integration, mixed technologies

## Additional Ideas

### 5. log_analyzer
**Purpose**: Parse and analyze log files
**Features**:
- Multi-format parsers (apache, nginx, json)
- Time-series aggregations
- Pattern matching and filtering
- Statistics and reports
- Export to various formats

**Shows**: File processing, regex, aggregations, streaming

### 6. task_manager
**Purpose**: Async job queue with state management
**Features**:
- Task submission and tracking
- Progress monitoring
- Retry logic
- Scheduling
- Background execution

**Shows**: Async operations, state management, queuing, concurrency

### 7. config_manager
**Purpose**: Multi-environment configuration management
**Features**:
- Environment profiles (dev, staging, prod)
- Template engine with variables
- Pydantic validation
- Secrets management
- Config inheritance

**Shows**: Validation, templating, security patterns

### 8. notification_hub
**Purpose**: Multi-channel notification system
**Features**:
- Multiple channels (email, slack, webhook, SMS)
- Template management
- Delivery tracking
- Rate limiting
- Error handling and retries

**Shows**: Integration patterns, async delivery, error handling

### 9. api_proxy
**Purpose**: API gateway/proxy with enhancements
**Features**:
- Request forwarding
- Response caching
- Rate limiting
- Authentication injection
- Request/response transformation

**Shows**: HTTP client patterns, caching, middleware, proxying

### 10. metrics_collector
**Purpose**: Metrics collection and monitoring
**Features**:
- Metric types (counter, gauge, histogram)
- Time-series aggregation
- Multiple export formats (Prometheus, JSON, Grafana)
- Alerting rules

**Shows**: Time-series data, aggregations, monitoring patterns

## Selection Criteria

Each demo should:
- ✅ **Be standalone** - Usable as library without smpub
- ✅ **Show different patterns** - Async, streaming, state, integrations
- ✅ **Be realistic** - Something people would actually use
- ✅ **Highlight SmartSwitch** - Show how it simplifies architecture
- ✅ **Have separate docs** - Like demo_shop
- ✅ **Be quick to publish** - Show that smpub makes it trivial

## Demo Structure Template

Each demo follows the same pattern:

```
examples/demo_<name>/
├── sample_<name>/          # Standalone library (no smpub dependency)
│   ├── __init__.py
│   ├── <main_class>.py    # Main class with Switcher
│   ├── core/              # Core components
│   ├── example_*.py       # Python usage examples
│   └── test_*.py          # Tests
│
├── published_<name>/       # smpub application (~20 lines)
│   ├── main.py            # Publisher
│   └── setup.py           # Optional setup script
│
├── docs/                  # Separate ReadTheDocs project
│   ├── conf.py
│   ├── index.md
│   └── ...
│
└── README.md              # Overview
```

## Key Messages

Each demo reinforces:

1. **"Your library is independent"** - No smpub in sample_* code
2. **"SmartSwitch structures your API"** - Clean dispatch pattern
3. **"Publishing is trivial"** - published_* is just ~20 lines
4. **"Get CLI + HTTP for free"** - No additional code needed

## Next Steps

1. Complete demo_shop documentation
2. Review and refine smpub docs (focus on app registration/usage)
3. Choose next demo based on:
   - Different patterns than demo_shop
   - Community interest
   - Real-world applicability

---

**Last Updated**: 2025-11-12
