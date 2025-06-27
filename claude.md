# CLAUDE.md - FanSale Automated Ticket Reservation Bot

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the FanSale ticket reservation system in this repository. The code i run the script from is fansale_check.md

## 🎯 Project Overview

This is an automated ticket monitoring and reservation bot for FanSale.it that operates **without login requirements**. The bot uses multiple concurrent browsers to maximize ticket detection speed and automatically reserves tickets matching user-defined criteria.

### Core Purpose
- Monitor FanSale.it ticket pages for available tickets
- Automatically click and reserve tickets based on user preferences (Prato A, B, Settore, etc.)
- Handle CAPTCHAs either automatically (via 2captcha) or with manual alerts
- Operate multiple browsers in parallel for maximum efficiency

## 🏗️ Architecture & Core Components

### 1. **Speed-Critical Ticket Detection Flow**
The bot's primary optimization is its parallel detection and instant reservation system:

```python
# Main ticket detection loop (hunt_tickets method, line ~1300)
- Check interval: 0.3-1.0 seconds (ultra-fast)
- Full page refresh: Every 15±3 seconds
- Session refresh: Every 15 minutes
- Multiple browsers: 1-8 concurrent instances
```

### 2. **Critical Selectors & Detection**

#### Ticket Detection (line ~1407)
```css
/* Primary selector */
div[data-qa='ticketToBuy']

/* Fallback selectors */
div[class*='ticket'][class*='available']
div[class*='biglietto'][class*='disponibile']
article[class*='ticket']
div[data-testid*='ticket']
```

#### Ticket Click Strategy (line ~1635)
1. JavaScript click on main element
2. Click specific FanSale link: `a.Button-inOfferEntryList, a[id*='detailBShowOfferButton']`
3. Click any child element: `a, button, [role='button']`
4. ActionChains click
5. Direct Selenium click

#### Buy Button Detection (line ~1675)
```python
# Priority order:
1. FanSale-specific: button[data-qa='buyNowButton']
2. Italian text: Acquista, Compra, Prenota, Procedi
3. Class-based: button[class*='buy'], button[class*='acquista']
4. English fallbacks: Buy, Purchase, Checkout
5. Generic submit buttons
```

### 3. **Thread Architecture**
- **Main Thread**: User interface, configuration, statistics
- **Hunter Threads**: One per browser, continuously scanning
- **Synchronization**:
  - `purchase_lock`: Ensures single purchase at a time
  - `shutdown_event`: Graceful shutdown
  - `StatsManager`: Thread-safe statistics with atomic operations

### 4. **Anti-Detection Mechanisms**

#### Browser Creation (create_browser, line ~1011)
- Undetected ChromeDriver with stealth JavaScript
- Persistent browser profiles for cookies/session
- Multi-version fallback (tries versions: None, 137, 138, 136, 135, 131, 130)
- Window positioning for multi-monitor setups

#### Stealth Features
- Removes webdriver property
- Mocks plugins and languages
- Handles Chrome runtime
- Removes automation indicators
- **IMAGES ENABLED** (verified on startup)

## 📋 Configuration System

### Environment Variables (.env)
```bash
FANSALE_TARGET_URL=https://www.fansale.it/tickets/all/event-name/...
TWOCAPTCHA_API_KEY=your_api_key_here  # Optional for auto-CAPTCHA
```

### Configuration Files
- `bot_config_v7.json`: Runtime configuration
- `fansale_stats_v7.json`: Persistent statistics
- `browser_profiles/`: Chrome profile storage

### Runtime Settings
```json
{
  "browsers_count": 2,      # Parallel browsers (1-8)
  "max_tickets": 2,         # Stop after securing this many
  "refresh_interval": 30,   # Full page refresh (seconds)
  "session_timeout": 900,   # Session refresh (15 min)
  "min_wait": 0.3,         # Min check interval
  "max_wait": 1.0          # Max check interval
}
```

## 🚀 Key Commands & Usage

```bash
# Setup
source venv/bin/activate
pip install -r requirements_v6.txt

# Run the bot
python3 fansale_check.py

# Fix Python 3.13 compatibility
pip install --force-reinstall setuptools
```

## 🔧 Critical Implementation Details

### Duplicate Detection (line ~720)
- MD5 hashing of ticket text (timestamps removed)
- Only new tickets trigger purchase flow
- Hash stored in `seen_tickets` set

### Purchase Flow
1. **Detect** new ticket → **Extract** info → **Check** if hunting type
2. **Click** ticket (multiple methods) → **Find** buy button → **Click** buy
3. **Handle** CAPTCHA if present → **Verify** navigation → **Screenshot**

### CAPTCHA Handling
- **Automatic**: 2captcha integration (if API key provided)
- **Manual**: Audio + visual alert, 120-second timeout
- **Grace Period**: 5 minutes after solving (no CAPTCHA checks)

### Performance Tracking
- Page load times
- Ticket check times
- Popup dismiss times
- Real-time statistics dashboard

## ⚠️ Important Patterns & Best Practices

### When Modifying Code

1. **Minimize DOM Interactions**
   ```python
   # Good: JavaScript execution
   driver.execute_script("arguments[0].click();", element)
   
   # Avoid: Multiple Selenium calls
   element.click()  # Only as fallback
   ```

2. **Thread Safety**
   ```python
   with self.purchase_lock:
       # Critical purchase code
   ```

3. **Error Handling**
   ```python
   @retry(max_attempts=2, delay=0.5)
   def critical_method():
       # Auto-retry on failure
   ```

4. **Logging Categories**
   - `prato_a`, `prato_b`, `settore`, `other`: Ticket types
   - `system`: General operations
   - Separate log files per category

### Debugging & Monitoring

- **Console**: Color-coded ticket types
- **Statistics**: Every 60 seconds dashboard update
- **Logs**: `fansale_v7_*.log` files per category
- **Screenshots**: `screenshots/` on successful purchases

## 🐛 Common Issues & Solutions

### Chrome Version Mismatch
- Bot tries multiple Chrome versions automatically
- Update Chrome to latest stable version
- Check `detect_chrome_version.py` for installed version

### CAPTCHA Issues
- Set `TWOCAPTCHA_API_KEY` for automatic solving
- Ensure speakers/audio enabled for manual alerts
- Check grace period is active after solving

### Performance Issues
- Reduce browser count if CPU constrained
- Increase wait times if rate-limited
- Check network stability

## 📊 Data Flow

1. **Input**: Target URL, ticket preferences, browser count
2. **Processing**: Parallel browsers → Ticket detection → Purchase attempts
3. **Output**: Reserved tickets, statistics, screenshots

## 🔒 Security & Safety

- **No login required**: Bot operates anonymously
- **No payment handling**: Stops at reservation
- **Session isolation**: Separate browser profiles
- **Data persistence**: Statistics saved atomically

## 💡 Tips for Maximum Success

1. **Multi-monitor setup**: Position browsers across screens
2. **Ticket selection**: Start with specific types (Prato A/B)
3. **Browser count**: 2-4 optimal for most systems
4. **Network**: Stable, low-latency connection critical
5. **CAPTCHA prep**: Have 2captcha credits or be ready to solve manually

## 🚨 IMPORTANT REMINDERS

- **NEVER** cache DOM elements (causes stale references)
- **ALWAYS** verify image loading on startup
- **CHECK** for popups/modals before critical actions
- **MONITOR** statistics dashboard for performance
- **TEST** with non-critical events first

## 📝 Code Modification Guidelines

When making changes:
1. Preserve thread safety (use locks)
2. Maintain logging structure (category-based)
3. Keep retry mechanisms for critical operations
4. Test with multiple browsers before committing
5. Update statistics tracking for new features

## 🔄 Version History

- **V7 (Current)**: Ultimate edition with all fixes
  - Correct environment variable handling
  - Enhanced popup dismissal
  - Improved ticket selection logic
  - Better CAPTCHA integration
  - Performance monitoring

Remember: This bot is optimized for SPEED and RELIABILITY. Every millisecond counts in the race to secure tickets!

## 🔍 Quick Reference - Key Methods & Line Numbers

### Core Methods
- `__init__` (line ~335): Bot initialization and configuration
- `create_browser` (line ~1011): Stealth browser creation with anti-detection
- `hunt_tickets` (line ~1300): Main hunting loop for each browser
- `purchase_ticket` (line ~1530): Ticket purchase attempt logic
- `detect_captcha` (line ~778): CAPTCHA detection strategies
- `dismiss_popups` (line ~588): Popup/modal handling
- `extract_full_ticket_info` (line ~475): Ticket data extraction
- `show_statistics_dashboard` (line ~1691): Live stats display

### Helper Methods
- `categorize_ticket` (line ~452): Classify ticket type (Prato A/B, Settore)
- `generate_ticket_hash` (line ~469): Create unique ticket identifier
- `wait_for_page_change` (line ~1526): Detect navigation success
- `handle_checkout_page` (line ~1538): Process checkout after buy click
- `verify_image_loading` (line ~399): Ensure images load properly

## 🎭 Testing & Development

### Test Scripts Available
- `test_fansale_v7.py`: Basic functionality tests
- `test_real_purchase_v7.py`: Full purchase flow testing
- `detect_chrome_version.py`: Chrome compatibility check
- `quick_test_v7.py`: Quick validation tests

### Development Workflow
1. Make changes to `fansale_check.py`
2. Test with single browser first: `browsers_count: 1`
3. Verify with `python3 -m py_compile fansale_check.py`
4. Run full test suite before committing
5. Update CLAUDE.md if adding new features

## 📦 Dependencies

```txt
# requirements_v6.txt
undetected-chromedriver>=3.5.0
selenium>=4.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

## 🌐 External Integrations

### 2Captcha Service
- API endpoint: `http://2captcha.com`
- Supported: reCAPTCHA v2, v3
- Token injection via JavaScript
- Automatic retry on failure

### FanSale.it Specifics
- No login required
- Ticket pages: `/tickets/all/...`
- Checkout flow: ticket → detail → buy → cart
- CAPTCHA appears randomly after buy click

## ⚡ Performance Benchmarks

- **Check rate**: 60-300 checks/minute (with 2 browsers)
- **Unique ticket detection**: ~1% of total found
- **Page load**: Target < 3 seconds
- **Buy click response**: < 1 second
- **CAPTCHA solve**: Manual ~30s, Auto ~20s

## 🔐 Important Security Notes

- This bot is for DEFENSIVE purposes only
- Does NOT handle payment information
- Does NOT store personal data
- Uses temporary browser profiles
- All actions are logged for audit

---

**Last Updated**: December 2024
**Main Script**: `fansale_check.py`
**Version**: 7.0 Ultimate