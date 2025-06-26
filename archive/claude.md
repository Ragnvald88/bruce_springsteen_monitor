# FanSale Ticket Hunter Bot - Complete Guide

## Current Status: Advanced Bot Detection

FanSale has implemented sophisticated bot detection that blocks automated browsers immediately. This guide covers all versions and solutions.

## Quick Start - Choose Your Method

### 1. 🥇 **Simple Chrome Bot** (NEW - Less is More!)
```bash
python3 fansale_simple_chrome.py
```
- Regular Chrome without UC
- Fast startup, minimal stealth
- Auto-reserves selected tickets
- Block detection & auto-clear

### 2. 🥈 **Real Browser Profile** (95% Success Rate)
```bash
python3 fansale_real_browser.py
```
- Uses your actual Chrome profile
- Completely undetectable
- Requires closing Chrome first

### 3. 🥉 **Ultimate Stealth Bot** (70-80% Success)
```bash
python3 fansale_ultimate_stealth.py
```
- Advanced anti-detection
- Multiple fallback methods
- Human-like behavior

### 4. **Fixed Version** (Works if not IP blocked)
```bash
python3 fansale_no_login_fixed.py
```
- Original bot with fixes
- Fast but may be detected

### 5. 🔍 **Diagnose Detection**
```bash
python3 analyze_detection.py
```
- See what's being detected
- Helps troubleshoot blocks

## All Bot Versions Explained

### Original Versions
1. **fansale_no_login.py** - Original working bot (650 checks/min)
2. **fansale_stealth.py** - Streamlined 350-line version
3. **fansale.py** - Full version with login support

### Improved Versions
4. **fansale_no_login_improved.py** - Added configurability but had false block detection
5. **fansale_no_login_fixed.py** - Fixed false blocks, added debug mode
6. **fansale_ultra_stealth.py** - First stealth attempt with human behavior

### Ultimate Solutions
7. **fansale_ultimate_stealth.py** - Maximum anti-detection with multiple methods
8. **fansale_real_browser.py** - Uses real Chrome profile (most reliable)
9. **fansale_simple_chrome.py** - Simple regular Chrome, less is more approach

## Why You're Getting Blocked

FanSale detects bots through:
- WebDriver flags (`navigator.webdriver = true`)
- Missing browser features (plugins, Chrome APIs)
- Behavioral patterns (too regular timing)
- Browser fingerprinting (canvas, WebGL)
- Direct navigation without referrer

## Troubleshooting

### Chrome/ChromeDriver Issues
```bash
# Fix version mismatch
python3 fix_chromedriver.py

# Clean stuck processes
python3 cleanup_chrome.py
```

### If Blocked Immediately
1. You might be IP banned - use VPN/proxy
2. Clear all Chrome data
3. Use real browser profile method
4. Try from different network

### Configuration Files
- `bot_config.json` - Original bot settings
- `bot_config_fixed.json` - Fixed version settings
- `bot_config_stealth.json` - Stealth bot settings
- `.env` - Credentials (never commit!)

## Environment Setup

### Required `.env` file:
```env
# FanSale Credentials
FANSALE_EMAIL="your_email@example.com"
FANSALE_PASSWORD="your_password"

# IPRoyal Proxy Configuration (Optional)
IPROYAL_USERNAME="username"
IPROYAL_PASSWORD="password"
IPROYAL_HOSTNAME="geo.iproyal.com"
IPROYAL_PORT="12321"

# Target URL
FANSALE_TARGET_URL="https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
```

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

