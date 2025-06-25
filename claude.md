# StealthMaster - High-Speed Ticket Bot

## Overview
StealthMaster is an ultra-fast ticket purchasing bot for FanSale.it, optimized for speed and stealth. It can perform 100-200 checks per minute per browser with no login required.

## Key Features
- **No Login Required**: Reserves tickets without authentication
- **Ultra-Fast**: 100-200 checks/minute per browser (200-400 with 2 browsers)
- **Multi-Browser**: Run 1-5 concurrent browsers
- **Stealth Mode**: Undetected Chrome with anti-detection measures
- **Smart Filtering**: Hunt specific ticket types (Prato A, Prato B, Settore)
- **Auto-Recovery**: Handles 404 blocks and session issues
- **Real-time Stats**: Live performance metrics and ticket tracking

## Project Structure
```
stealthmaster/
├── fansale_no_login.py      # Main bot (optimized, no login)
├── fansale_stealth.py        # Streamlined 350-line version
├── fansale.py                # Original full-featured version
├── bot_config.json           # Configuration settings
├── fansale_stats.json        # Persistent statistics
├── fix_distutils.py          # Python 3.13 compatibility
├── fix_chromedriver.py       # ChromeDriver version fixer
├── cleanup_chrome.py         # Kill stuck Chrome processes
├── quick_test.py             # Quick functionality test
└── utilities/                # Enhanced features directory
```

## Quick Start

### 1. Prerequisites
- Python 3.13+
- Google Chrome installed
- macOS/Windows/Linux

### 2. Installation
```bash
pip3 install -r requirements.txt
```

### 3. Fix ChromeDriver (if needed)
```bash
python3 fix_chromedriver.py
```

### 4. Run the Bot
```bash
python3 fansale_no_login.py
```

Press `1` to start hunting immediately with saved settings.

## Configuration

### bot_config.json
```json
{
  "browsers_count": 2,
  "max_tickets": 4,
  "min_wait": 0.05,
  "max_wait": 0.1,
  "ticket_types_to_hunt": ["prato_a", "prato_b"]
}
```

### Ticket Types
- `prato_a` - Standing area (front) - Red alerts 🔴
- `prato_b` - Standing area (back) - Blue alerts 🔵
- `settore` - Seated sections - Yellow alerts 🟡

## Performance Optimizations

### Speed Achievements
- **Main Loop**: 50ms delay (was 2.5-3.5s)
- **Browser Creation**: Single version attempt (was 3 attempts)
- **Navigation**: 0.8-1.2s wait (was 2-3s)
- **Session Checks**: Every 100 iterations (was every 10)

### Expected Performance
- 100-200 checks/minute per browser
- < 100ms ticket detection
- < 500ms from detection to click
- 2-5 seconds browser startup

## Troubleshooting

### Browser Creation Failed
```bash
python3 cleanup_chrome.py
python3 fix_chromedriver.py
```

### Python 3.13 Issues
The `fix_distutils.py` is automatically imported to handle compatibility.

### Session Errors
Increase delays in `bot_config.json` if getting rate-limited.

## Architecture

### Core Components
1. **FanSaleBot**: Main bot class with all logic
2. **BotConfig**: Configuration management
3. **StatsManager**: Thread-safe statistics
4. **NotificationManager**: System notifications
5. **HealthMonitor**: Session health tracking

### Detection Flow
1. Navigate to event page
2. Find ticket elements
3. Extract ticket information
4. Categorize by type
5. Check for duplicates
6. Log if new
7. Attempt purchase if hunting

### Anti-Detection Features
- Undetected ChromeDriver
- Randomized delays
- Browser profiles
- JavaScript stealth injection
- User-agent spoofing

## Advanced Usage

### Custom Target URL
Set environment variable:
```bash
export FANSALE_TARGET_URL="https://www.fansale.it/..."
```

### Debug Mode
Enable detailed logging in the script.

### Multi-Monitor Setup
Browsers automatically position across monitors.

## Files Reference

### Essential Files
- `fansale_no_login.py` - Main bot to run
- `bot_config.json` - Settings
- `fix_chromedriver.py` - Fix Chrome issues
- `cleanup_chrome.py` - Clean stuck processes

### Data Files
- `fansale_stats.json` - Performance statistics
- `browser_profiles/` - Browser data
- `screenshots/` - Purchase screenshots

## Notes
- Optimized for FanSale.it only
- Not designed for other platforms (yet)
- Respect rate limits to avoid blocks
- Use responsibly

Last updated: June 2025
