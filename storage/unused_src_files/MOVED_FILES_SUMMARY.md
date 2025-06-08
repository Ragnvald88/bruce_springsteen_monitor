# Unused Source Files Summary

This directory contains files that were moved from the `src/` directory because they are not part of the active execution path starting from `main.py`.

## Files Moved on 2025-06-08

### Test Files
- `test_stealthmaster.py` - Main test file
- `testing/comprehensive_test_suite.py` - Comprehensive test suite
- `testing/performance_comparison.py` - Performance comparison tests
- `testing/realistic_performance_test.py` - Realistic performance tests

### Unused Core Components
- `core/browser_pool.py` - Browser pool management (not used in v3)
- `core/managers.py` - Various managers (replaced by orchestrator)
- `core/proxy_manager.py` - Proxy management (functionality integrated elsewhere)
- `core/strike_force.py` - Strike force implementation (not currently active)
- `core/ticket_reserver.py` - Ticket reservation logic (not implemented)
- `core/ui/gui_advanced.py` - Advanced GUI (not used)
- `core/ui/detection_dashboard.py` - Detection dashboard UI (replaced)

### Unused Stealth Components
- `stealth/cdp_stealth.py` - CDP stealth implementation
- `stealth/session_persistence.py` - Session persistence logic
- `stealth/stealth_engine.py` - Stealth engine implementation
- `stealth/stealth_integration.py` - Stealth integration module
- `stealth/ultra_stealth.py` - Ultra stealth features

### Unused UI Components
- `ui/enhanced_detection_monitor.py` - Enhanced detection monitor

### Unused Utils
- `utils/enhanced_logger.py` - Enhanced logging utilities
- `utils/live_status_logger.py` - Live status logging
- `utils/notifier.py` - Notification system
- `utils/retry_utils.py` - Retry utilities
- `utils/stealth_tester.py` - Stealth testing utilities

### Other
- `templates/` - HTML templates directory

## Active Files Remaining in src/

The following files are actively used by the main execution path:

- Core execution: `main.py`, `core/orchestrator.py`
- Browser/stealth: `core/stealth_browser_launcher.py`, `stealth/advanced_fingerprint.py`
- Behavior: `core/human_behavior_engine.py`, `core/adaptive_scheduler.py`
- Rate limiting: `core/rate_limiter.py`
- Models/types: `core/models.py`, `core/enums.py`, `core/errors.py`
- Monitoring: `core/detection_monitor.py`
- Platform handling: `platforms/unified_handler.py`
- Profile management: `profiles/manager.py`, `profiles/models.py`, `profiles/utils.py`, `profiles/consilidated_models.py`

These files can be restored to their original locations if needed by moving them back from this storage directory.