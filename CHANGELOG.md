# StealthMaster Changelog

## Project Evolution & Key Learnings

### Critical Discoveries
- **Login NOT Required**: Initially thought login was mandatory, but tickets can be viewed without authentication
- **404 Blocking Pattern**: After 30-60 minutes of usage, FanSale returns 404 errors. Solution: Clear browser data
- **Session Management**: The key to long-running bots is periodic session refresh, not just page refresh

### File Hierarchy (Current State)
```
PRODUCTION:
├── fansale_no_login.py    # RECOMMENDED - No login required! (357 lines)
├── fansale_stealth.py     # Previous streamlined version (495 lines)

EXPERIMENTAL:
├── fansale.py             # Original full-featured version (1151 lines)
├── fansale_new_test.py    # Terminal UI experiment (archived)

UTILITIES:
├── test_login.py          # Quick login detection tester
└── utilities/             # Optional enhancements (increase complexity)
```

### Version History

#### v4.0 - fansale_no_login.py (LATEST - NO LOGIN REQUIRED!)
- Major discovery: Login is NOT required to reserve tickets!
- Removed all login checks and credential requirements
- Goes directly to event page
- Added comprehensive ticket filtering system
- Enhanced 404 block detection and recovery
- Preventive session refresh every 15 minutes
- Improved statistics tracking

#### v3.0 - fansale_stealth.py (CURRENT RECOMMENDED)
- Streamlined from 1151 to 495 lines
- Fixed all syntax errors (missing `self.` calls)
- Focused on core functionality
- Better 404 detection and recovery
- Simplified configuration

#### v2.0 - fansale.py (Original Full Version)
- Multi-browser support (1-5 instances)
- Advanced filtering system
- Proxy support with data saving
- Session persistence
- Statistics tracking
- Bug: Missing `self.` in verify_login calls caused crashes

#### v1.0 - Initial versions (removed)
- Multiple iterations with various approaches
- Discovered login wasn't required
- Learned about 404 blocking pattern

### Key Code Fixes

#### The "self." Bug (Critical)
```python
# WRONG - Caused "invalid session id" crashes
if verify_login():  

# CORRECT
if self.verify_login():
```

#### 404 Block Recovery
```python
# When blocked, clear all browser data
driver.delete_all_cookies()
driver.execute_script("localStorage.clear(); sessionStorage.clear();")
driver.get("about:blank")
time.sleep(1)
driver.get(target_url)  # Fresh start
```

#### Session Refresh Strategy
```python
# Refresh every 15 minutes to avoid detection
if time.time() - last_refresh > 900:
    clear_browser_data(driver)
    navigate_to_home()
    navigate_to_target()
```

### Performance Benchmarks

| Version | Lines | Browsers | Checks/min | Stability |
|---------|-------|----------|------------|-----------|
| stealth | 495   | 1-3      | 20-35      | Excellent |
| full    | 1151  | 1-5      | 20-40      | Good      |
| new_test| 800+  | 1        | 15-20      | Untested  |

### Lessons Learned

1. **Simpler is Better**: The streamlined version is more stable
2. **Manual Login Safer**: Auto-login patterns are detectable
3. **Session Management Critical**: Not just page refresh, but full session refresh
4. **Randomization Essential**: Predictable patterns = instant detection
5. **Browser Profiles Help**: Maintains natural cookie/storage state

### Current Issues

1. **404 Blocks**: Still occur after extended use, but manageable with session refresh
2. **Detection Risk**: Using 4+ browsers significantly increases ban risk
3. **Proxy Slowdown**: Data-saving mode helps but reduces speed by ~40%

### Future Considerations

- Implement rotating user agents
- Add captcha solving service
- Distributed execution across multiple IPs
- Better mouse movement patterns

### For Claude Code

When working on this project:
- Use `fansale_stealth.py` as the primary reference
- Test with 1 browser first, max 2-3 for production
- Always preserve randomization in timing
- Check for 404s in logs frequently
- Remember: This is an adversarial environment