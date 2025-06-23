# StealthMaster - Claude Code Guide

## Quick Start
**Use `fansale_no_login.py`** - The latest version that doesn't require login!

## Project Purpose
A ticket purchasing bot for FanSale.it that uses undetected-chromedriver to avoid bot detection while monitoring and purchasing concert tickets. Works WITHOUT login!

## Key Files
```
fansale_no_login.py    # ← USE THIS (no login required!)
fansale_stealth.py     # Previous version (requires login)
fansale.py            # Original full version (requires login)
test_login.py         # Login detection test
CHANGELOG.md          # Project history & lessons learned
```

## Critical Knowledge

### 1. Login NOT Required!
User discovered tickets can be reserved WITHOUT authentication. The bot now goes directly to the event page.

### 2. The 404 Block Pattern
After 30-60 minutes, FanSale returns 404 errors. This is their anti-bot measure.
```python
# Solution: Clear browser data and refresh
driver.delete_all_cookies()
driver.execute_script("localStorage.clear(); sessionStorage.clear();")
```

### 2. Login is Optional
Despite initial assumptions, tickets can be viewed without login. Manual login is safer than automation.

### 3. Timing is Everything
```python
# These delays are battle-tested - don't reduce them
refresh_delay = random.uniform(2.5, 3.5)  # Between checks
full_refresh_every = 30  # seconds
session_refresh = 900    # 15 minutes
```

### 4. Common Pitfalls to Avoid
- Don't use more than 2-3 browsers (detection risk)
- Don't remove randomization (predictable = banned)
- Don't skip session refreshes (leads to 404s)
- Always use `self.` with method calls

## Italian Venue Terminology
- `Prato` = Lawn/standing area (e.g., "Prato A")
- `Tribuna` = Tribune/stands  
- `Parterre` = Floor/pit area
- `Settore` = Sector
- `Numerato` = Numbered seats

## Development Workflow
1. Test changes with `test_login.py` first
2. Run with 1 browser initially
3. Monitor `fansale_bot.log` for 404s or blocks
4. Check `debug.log` for detailed troubleshooting

## Environment Setup
```bash
# .env file (only URL needed!)
FANSALE_TARGET_URL=https://www.fansale.it/...

# Install dependencies
pip install undetected-chromedriver selenium python-dotenv
```

## Testing Commands
```bash
# Run the no-login bot (RECOMMENDED)
python fansale_no_login.py

# Run previous versions (require login)
python fansale_stealth.py
python fansale.py

# Test login detection
python test_login.py
```

## Performance Expectations
- 1 browser: ~20 checks/minute (safest)
- 2 browsers: ~30 checks/minute (recommended max)
- 3+ browsers: Higher detection risk

## When Things Go Wrong
1. **404 Errors**: Clear browser profiles: `rm -rf browser_profiles/`
2. **Login Issues**: Use manual login option
3. **Slow Performance**: Disable proxy if not needed
4. **High CPU**: Reduce browser count

## See Also
- `CHANGELOG.md` - Detailed version history and lessons learned
- `stats.json` - Performance metrics from runs
- `screenshots/` - Successful ticket captures

## Remember
This operates in an adversarial environment. FanSale actively tries to detect and block bots. Every optimization must balance speed with stealth. When in doubt, choose stealth over speed.