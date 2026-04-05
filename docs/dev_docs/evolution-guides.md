---
layout: default
title: Evolution Guides
---

This document provides guidance for evolving and extending the Prism architecture, including migration paths, extension mechanisms, and best practices for maintaining the clean, immutable, DI-driven design.

## Capability Evolution Framework

Prism implements a pluggable extension system that allows dynamic loading of capabilities through a registry-based approach.

### Extension Registry

The extension registry supports:

- Dynamic loading of plugins
- Version compatibility handling
- Isolation of extensions

To add a new capability:

1. Implement the extension interface
2. Register it in the extension registry
3. Configure via strategy selection

### Plugin System

Prism exposes plugin interfaces and defaults, but the registry is currently
utility-only and not wired into the scanner runtime path by default.

Supported runtime plugin seam for this cycle:

- **VariableDiscoveryPlugin**: Handles variable discovery (static, referenced, type inference, unresolved resolution)
- **FeatureDetectionPlugin**: Analyzes role features (tasks, handlers, collections, etc.)

Interfaces for `OutputOrchestrationPlugin` and `ScanPipelinePlugin` remain
available, but they are not selected by scanner runtime wiring unless you add
an explicit integration seam.

#### Creating a Custom Plugin

```python
from prism.scanner_plugins.interfaces import VariableDiscoveryPlugin

class MyVariableDiscoveryPlugin(VariableDiscoveryPlugin):
    def discover_static_variables(self, role_path: str, options: dict) -> tuple:
        # Custom implementation
        return ()

    def discover_referenced_variables(self, role_path: str, options: dict, readme_content: str | None = None) -> frozenset:
        # Custom implementation
        return frozenset()

    def resolve_unresolved_variables(self, static_names: frozenset, referenced: frozenset, options: dict) -> dict:
        # Custom implementation
        return {}
```

#### Registering a Plugin (Utility Registry)

```python
from prism.scanner_plugins.registry import plugin_registry

plugin_registry.register_variable_discovery_plugin("my_plugin", MyVariableDiscoveryPlugin)
```

Registry registration above is for utility/discovery workflows and does not
automatically activate runtime scan behavior.

#### Configuring Runtime Plugin Overrides

Set plugin factory overrides on `DIContainer` when you explicitly want runtime
plugin behavior. Current runtime wiring honors `variable_discovery_plugin_factory`
and `feature_detection_plugin_factory` overrides.

```python
from prism.scanner_core.di import DIContainer

container = DIContainer(
    role_path="/path/to/role",
    scan_options={"include_vars_main": True},
    factory_overrides={
        "variable_discovery_plugin_factory": lambda role_path, options: MyVariableDiscoveryPlugin(container),
        "feature_detection_plugin_factory": lambda role_path, options: MyFeaturePlugin(container),
    },
)
```

### Strategy Patterns

Major behaviors are implemented as strategy patterns:

- Default strategies provided out-of-the-box
- Configuration-driven selection
- Easy replacement for custom implementations

## Migration Guides

### From Procedural to Functional Pipelines

**Old Approach:**

```python
def process_data(data):
    data['field'] = transform(data['field'])  # Mutation
    return data
```

**New Approach:**

```python
def process_data(data: DataDict) -> DataDict:
    return data | {'field': transform(data['field'])}  # Immutable
```

### Eliminating Global State

**Anti-pattern:**

```python
global_config = {}

def set_config(config):
    global global_config
    global_config.update(config)
```

**Correct Pattern:**

```python
@dataclass(frozen=True)
class Config:
    settings: dict

def process_with_config(data, config: Config):
    # Use config.settings
    pass
```

### DI Container Usage

Inject dependencies explicitly:

```python
class Processor:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger

# In DI container
def create_processor() -> Processor:
    return Processor(
        config=di_container.get_config(),
        logger=di_container.get_logger()
    )
```

## Extension Development

### Adding New Variable Discovery Strategies

1. Implement `VariableDiscoveryStrategy` interface
2. Register in `DIContainer.factory_variable_discovery`
3. Configure via policy settings

### Custom Output Renderers

1. Implement `OutputRenderer` interface
2. Add to strategy registry
3. Select via configuration

## Backward Compatibility

- Deprecation warnings for old APIs
- Migration paths provided
- Rollback mechanisms available

## Best Practices

- Maintain immutability in all data flows
- Use DI for all dependencies
- Write pure functions where possible
- Add comprehensive tests for extensions
- Document extension points clearly
