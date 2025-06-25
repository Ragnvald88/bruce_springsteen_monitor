# StealthMaster Bot Analysis & Improvement Plan

## Current Issues Identified

### 1. Menu System Issue
**Problem**: When selecting option 1 (Start Hunting), the bot still calls `configure()` method which asks for browser settings.

**Root Cause**: In the `run()` method:
```python
# Configure if first run
if not hasattr(self, '_configured'):
    self.configure()
    self._configured = True
```

This logic is flawed because `_configured` is never set elsewhere, so it always runs configure().

### 2. Browser Session Errors
**Problem**: `InvalidSessionIdException: session deleted as the browser has closed`

**Possible Causes**:
- Chrome/ChromeDriver version mismatch
- Browser being detected as automated
- Insufficient delays or improper initialization
- Missing stealth configurations

### 3. Performance Issues
**Current Performance**: Unknown - needs benchmarking

**Target Performance**:
- Browser creation: < 5 seconds per browser
- Page load: < 3 seconds
- Check rate: > 20 checks/minute per browser
- Ticket detection to reservation: < 2 seconds

## Improvement Plan

### Phase 1: Fix Menu System (Priority: Critical)

1. **Remove automatic configure() call**
   - Only configure when explicitly selected from menu
   - Load saved settings from bot_config.json on startup
   - Use defaults if no config exists

2. **Persist settings properly**
   - Save all settings to bot_config.json
   - Load on startup
   - Only show configure screen when option 2 is selected

### Phase 2: Fix Browser Stability (Priority: Critical)

1. **Improve browser creation**
   - Add better error handling
   - Implement retry logic with different configurations
   - Add health checks after creation

2. **Add browser stability features**
   - Keep-alive mechanism
   - Session validation before actions
   - Automatic recovery on failure

### Phase 3: Performance Optimization (Priority: High)

1. **Reduce unnecessary delays**
   - Current: 2.5-3.5 second waits
   - Target: 0.5-1.5 second waits where safe

2. **Optimize ticket checking**
   - Use more efficient selectors
   - Reduce DOM queries
   - Cache static elements

3. **Parallel processing**
   - Better thread management
   - Shared state optimization

### Phase 4: Code Cleanup (Priority: Medium)

1. **Remove redundant files**
   - Test files
   - Old backup versions
   - Temporary fix scripts

2. **Consolidate utilities**
   - Merge similar functionality
   - Remove unused imports

## Implementation Steps

### Step 1: Fix Menu System
```python
# Changes needed:
1. Remove _configured check from run()
2. Load config in __init__
3. Only show configure when option 2 selected
```

### Step 2: Fix Browser Creation
```python
# Improvements:
1. Add health check after creation
2. Better error recovery
3. Session validation
```

### Step 3: Add Benchmarking
```python
# Metrics to track:
- Browser creation time
- Page load time
- Checks per minute
- Time to detect new ticket
- Time from detection to reservation
```

### Step 4: Performance Optimization
```python
# Optimizations:
- Reduce sleeps where safe
- Cache selectors
- Optimize loops
```

## Success Criteria

### Benchmark Targets
1. **Stability**: 0 browser crashes in 1 hour
2. **Speed**: 30+ checks/minute per browser
3. **Detection**: < 500ms to identify new ticket
4. **Reservation**: < 2 seconds from detection to click
5. **Resource Usage**: < 500MB RAM per browser

### Testing Plan
1. Run for 5 minutes - verify no crashes
2. Run for 30 minutes - check performance metrics
3. Run for 2 hours - verify long-term stability

## Files to Remove (After Implementation)
- enhance_logging.py
- test_browser.py
- test_*.py files
- Old fix_*.py scripts

## Next Steps
1. Implement menu fix (10 minutes)
2. Test and verify (5 minutes)
3. Implement browser stability (20 minutes)
4. Add benchmarking (15 minutes)
5. Run tests and optimize (30 minutes)
6. Clean up files (10 minutes)
7. Update claude.md (10 minutes)

Total estimated time: ~100 minutes
