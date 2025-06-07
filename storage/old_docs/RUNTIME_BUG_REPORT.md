# Runtime Bug Report for Bruce Springsteen Ticket Monitor

## Executive Summary

The main.py file has several runtime bugs that prevent proper execution. The primary issues are:

1. **Platform Enum Conflicts** - Multiple conflicting Platform enum definitions
2. **Missing stealth module __init__.py** - Fixed during testing
3. **Attribute errors in monitoring loop** - Platform objects missing expected attributes
4. **Configuration issues** - Email field not populated in config.yaml

## Detailed Bug Analysis

### 1. Platform Enum Conflicts (CRITICAL)

**Issue**: There are multiple Platform enum definitions across the codebase:
- `src/models/enums.py` - Simple enum without methods
- `src/profiles/consolidated_models.py` - Enum with methods like `requires_stealth()`
- `src/core/enums.py` - Another Platform definition

**Error**: `'Platform' object has no attribute 'requires_stealth'`

**Location**: Profile scoring system expects Platform with methods but receives simple enum

**Fix Required**: Standardize on one Platform enum or ensure proper type conversion

### 2. Authentication Configuration (IMPORTANT)

**Issue**: The config.yaml has incomplete authentication credentials:
- `email:` field is empty (only password is populated)
- Environment variables are set but config takes precedence

**Impact**: Authentication will fail despite environment variables being set

**Fix Required**: Either populate email in config.yaml or modify code to prioritize env vars

### 3. Import Structure (FIXED)

**Issue**: Missing `__init__.py` in `src/core/stealth/` directory
**Status**: Fixed during testing by creating proper __init__.py

### 4. Browser Visibility (WORKING)

**Status**: ✓ Correctly configured
- `headless: false` in config.yaml
- Users will see browser windows during operation

### 5. Monitoring Loop Errors (CRITICAL)

**Issue**: Monitor tasks fail immediately with Platform attribute errors
**Error Log**:
```
Monitor error for Bruce Springsteen Milano 2025 (FS): 'Platform' object has no attribute 'requires_stealth'
```

## Test Results Summary

✓ **Working Components**:
- Basic imports and module loading
- Configuration loading
- Logging setup
- Playwright initialization
- Orchestrator creation
- Profile manager initialization
- Browser visibility settings
- Environment variables present

✗ **Failing Components**:
- Monitoring loop (Platform enum issues)
- Profile scoring (expects different Platform type)
- Authentication config (missing email)

## Quick Fixes

### Fix 1: Add email to config.yaml
```yaml
authentication:
  platforms:
    fansale:
      email: "your-email@example.com"  # Add this line
      password: "your-password"
```

### Fix 2: Temporary Platform enum fix
Create a wrapper or ensure consistent Platform usage across modules.

### Fix 3: Prioritize environment variables
Modify fansale.py to check env vars first:
```python
email = os.getenv('FANSALE_EMAIL') or auth_config.get('email')
password = os.getenv('FANSALE_PASSWORD') or auth_config.get('password')
```

## Recommendations

1. **Immediate**: Fix the Platform enum conflict by standardizing on one implementation
2. **High Priority**: Complete authentication configuration
3. **Medium Priority**: Add comprehensive error handling in monitoring loop
4. **Low Priority**: Clean up duplicate/unused enum definitions

## Testing Commands

```bash
# Test basic functionality
python src/main.py --help

# Test with dry run (safer)
python src/main.py --dry-run

# Test imports
python test_runtime_issues.py

# Check browser visibility
python test_browser_visibility.py
```

## Environment Status

- Python 3.13.2 ✓
- Playwright installed ✓
- .env file present with credentials ✓
- Config file valid YAML ✓
- All required directories exist ✓