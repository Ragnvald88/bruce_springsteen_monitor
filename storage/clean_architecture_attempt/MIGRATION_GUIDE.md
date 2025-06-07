# Migration Guide: Clean Architecture

## Overview

This guide explains the migration from the old monolithic structure to the new clean architecture.

## New Architecture Structure

```
src/
├── domain/           # Core business logic (no dependencies)
│   ├── entities/     # Core models (Platform, Profile, Ticket, Proxy)
│   └── services/     # Business rules (ProfileScoring, etc.)
│
├── application/      # Use cases and orchestration
│   ├── config.py     # Application configuration
│   └── use_cases/    # Application-specific logic
│
├── infrastructure/   # External services
│   ├── browser/      # Browser automation
│   ├── network/      # HTTP clients
│   ├── persistence/  # Data storage
│   └── monitoring/   # Monitoring services
│
├── presentation/     # User interfaces
│   ├── cli.py        # Command-line interface
│   └── ui/           # GUI components
│
└── adapters/         # Bridges between old and new code
    ├── platform_adapter.py
    └── profile_adapter.py
```

## Key Changes

### 1. Unified Model System

**Old Structure:**
- Multiple model definitions in `src/models/` and `src/profiles/`
- Conflicting enum definitions
- Complex import chains

**New Structure:**
- Single source of truth in `src/domain/entities/`
- Clear entity definitions with no external dependencies
- Simple, predictable imports

### 2. Platform Handling

**Old:**
```python
from src.profiles.enums import Platform
from src.core.enums import PlatformType
# Confusion about which to use
```

**New:**
```python
from domain.entities import Platform, PlatformType
# Single, clear import
```

### 3. Profile Management

**Old:**
```python
# Multiple profile models with different fields
from src.models.browser import BrowserProfile
from src.profiles.models import BrowserProfile as ProfilesBrowserProfile
```

**New:**
```python
from domain.entities import BrowserProfile
# One unified profile model
```

## Migration Steps

### Step 1: Use Adapters for Gradual Migration

The adapters help bridge old code to new entities:

```python
from adapters.platform_adapter import PlatformAdapter
from adapters.profile_adapter import ProfileAdapter

# Convert old platform enum to new entity
old_platform = OldPlatformEnum.FANSALE
new_platform = PlatformAdapter.from_old_enum(old_platform)

# Convert old profile to new entity
old_profile = legacy_profile_manager.get_profile()
new_profile = ProfileAdapter.from_old_profile(old_profile)
```

### Step 2: Update Imports Gradually

Replace old imports with new ones:

```python
# Old
from src.profiles.consolidated_models import Platform

# New
from domain.entities import Platform
```

### Step 3: Use New Configuration System

```python
from application.config import ApplicationConfig

# Load from YAML
config = ApplicationConfig.from_yaml("config/config.yaml")

# Validate
errors = config.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
```

## Benefits of Clean Architecture

1. **Clear Dependencies**: Domain entities have no external dependencies
2. **Testability**: Each layer can be tested independently
3. **Maintainability**: Clear separation of concerns
4. **Flexibility**: Easy to swap implementations (e.g., different browsers)
5. **Scalability**: Easy to add new features without affecting core logic

## Running the Application

### Using the New Architecture

```bash
python src/main_clean.py
```

### Using the Old Architecture (Compatibility Mode)

```bash
python src/main.py
```

## Troubleshooting

### Import Errors

If you see import errors, ensure:
1. You're running from the project root
2. The PYTHONPATH includes the src directory
3. You're using the correct import style (no relative imports in main scripts)

### Missing Dependencies

The new architecture uses the same dependencies as before. No new packages required.

### Configuration Issues

The new configuration system reads the same YAML files but provides better validation.
Check the output for specific configuration errors.

## Next Steps

1. Gradually migrate platform-specific code to infrastructure layer
2. Move browser automation to infrastructure/browser
3. Implement proper use cases in application layer
4. Add comprehensive tests for each layer

## Quick Reference

| Old Import | New Import |
|------------|------------|
| `src.profiles.consolidated_models.Platform` | `domain.entities.Platform` |
| `src.profiles.models.BrowserProfile` | `domain.entities.BrowserProfile` |
| `src.core.enums.PlatformType` | `domain.entities.PlatformType` |
| `src.models.proxy.ProxyConfig` | `domain.entities.ProxyConfig` |