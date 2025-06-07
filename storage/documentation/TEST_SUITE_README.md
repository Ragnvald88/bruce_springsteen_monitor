# Bruce Springsteen Ticket Monitor - Test Suite

This comprehensive test suite helps identify bugs and validate the functionality of the ticket monitoring system.

## Test Scripts Overview

### 1. **quick_health_check.py**
Quick system health check that verifies:
- Configuration file validity
- Required Python packages
- File structure integrity
- Stealth components
- File permissions

**Run this first to check basic system readiness:**
```bash
python Testing_Scripts/quick_health_check.py
```

### 2. **test_monitor_functionality.py**
Tests the core monitoring functionality:
- URL accessibility for each platform
- Opportunity detection parsing
- Detection patterns validation
- Data usage tracking
- Monitor initialization

**Output:** `test_monitor_report.yaml`

### 3. **test_profile_manager.py**
Tests the profile management system:
- Profile creation for each platform
- Profile selection algorithms
- Profile scoring system
- Platform assignment
- Session backup/restore

**Output:** `test_profile_manager_report.yaml`

### 4. **test_strike_force.py**
Tests the strike execution system:
- Strike parameter generation for different modes
- Profile selection for strikes
- Mock strike execution
- Platform-specific strategies

**Output:** `test_strike_force_report.yaml`

### 5. **test_full_integration.py**
Tests the complete system integration:
- Orchestrator initialization
- Subsystem initialization
- Full monitoring flow
- Opportunity queueing
- Strike execution flow
- Performance metrics

**Output:** `test_full_integration_report.yaml`

### 6. **Testing_Scripts/run_all_tests.py**
Master test runner that:
- Runs all test suites sequentially
- Collects and analyzes results
- Identifies bugs by severity
- Generates recommendations
- Creates comprehensive report

**Output:** `master_test_report.yaml` and `master_test_report.log`

## Running the Tests

### Quick Check
```bash
# Run quick health check first
python Testing_Scripts/quick_health_check.py
```

### Individual Tests
```bash
# Test specific components
python test_monitor_functionality.py
python test_profile_manager.py
python test_strike_force.py
python test_full_integration.py
```

### Full Test Suite
```bash
# Run all tests and generate master report
python run_all_tests.py
```

## Common Issues Detected

### 1. **URL Accessibility Issues**
- **Symptom:** Platform URLs return non-200 status codes
- **Fix:** Update URLs in `config/config.yaml` to current valid URLs

### 2. **Missing Detection Patterns**
- **Symptom:** No opportunities detected despite tickets being available
- **Fix:** Update detection patterns in monitor configuration

### 3. **Profile Creation Failures**
- **Symptom:** No profiles created or empty profile pools
- **Fix:** Check proxy configuration and profile manager settings

### 4. **Missing Environment Variables**
- **Symptom:** Config contains ${VAR_NAME} placeholders
- **Fix:** Set required environment variables or update config

### 5. **Stealth Components Missing**
- **Symptom:** Stealth files not found in src/core/stealth/
- **Fix:** Ensure all stealth components are properly placed

## Bug Severity Levels

- **CRITICAL:** System cannot run (initialization failures, missing core components)
- **HIGH:** Major functionality impaired (platform strategies missing, no profiles)
- **MEDIUM:** Reduced functionality (pattern mismatches, performance issues)
- **LOW:** Minor issues (warnings, optimization suggestions)

## Test Reports

Each test generates a YAML report containing:
- Test execution results
- Detected issues
- Performance metrics
- Component status

The master report (`master_test_report.yaml`) provides:
- Aggregated results from all tests
- Categorized bug list
- System readiness assessment
- Prioritized recommendations

## Troubleshooting

### Tests Won't Run
1. Check Python version (3.8+ required)
2. Install requirements: `pip install -r requirements.txt`
3. Ensure you're in the project root directory

### Import Errors
1. Add project to Python path
2. Check `__init__.py` files exist in all packages
3. Verify file structure matches expected layout

### Playwright Issues
- Tests will use mocks if Playwright not installed
- For full browser testing: `playwright install chromium`

### Permission Errors
- Ensure logs/, storage/, and session_backups/ directories are writable
- Make test scripts executable: `chmod +x *.py`

## Next Steps After Testing

1. **Fix CRITICAL bugs first** - System won't run without these
2. **Address HIGH priority issues** - Major functionality affected
3. **Update configuration** - Fix URLs, patterns, and settings
4. **Set environment variables** - For proxy and authentication
5. **Run system** - `python src/main.py` when all critical issues resolved

## Support

For issues with the test suite:
1. Check the master test report for detailed error information
2. Review individual test reports for component-specific issues
3. Enable debug logging for more details
4. Check system logs in the `logs/` directory