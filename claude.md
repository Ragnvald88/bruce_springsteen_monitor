# FanSale Ticket Hunter Bot - Fixed Version

## Overview
The FanSale Ticket Hunter Bot is an automated ticket purchasing system for FanSale.it, designed to monitor and secure tickets for concerts and events. 

## Recent Fixes (Critical)

### 1. **Fixed False Block Detection**
- **Problem**: Bot was detecting normal pages as blocked
- **Solution**: Now uses exact same logic as original bot:
  - Only checks for real 404/error patterns
  - Excludes "non sono state trovate" (no tickets found)
  - Checks Italian error messages properly
  - Block checking reduced to every 30 seconds

### 2. **Eliminated Popups**
- Added comprehensive popup prevention flags:
  - `--disable-notifications`
  - `--disable-save-password-bubble`
  - `--disable-translate`
  - `--disable-infobars`
  - Proper preferences to block all popups

### 3. **Fast Ticket Purchasing**
- Immediate clicking when ticket found
- No unnecessary delays
- Scrolls ticket into view first
- Takes screenshot on purchase attempt
- Clear logging of each step

### 4. **Debug Mode**
- Toggle from menu (option 4)
- Shows ticket detection status
- Helps verify bot is seeing tickets
- Useful for troubleshooting

## Quick Start

### Running the Fixed Bot
```bash
python3 fansale_no_login_fixed.py
```

### Recommended Settings
Start with Conservative or Balanced mode:
- **Conservative**: 60 checks/min (safest)
- **Balanced**: 120 checks/min (recommended)
- **Aggressive**: 240+ checks/min (monitor for blocks)

### Menu Options
1. **Start Hunting** - Begin monitoring
2. **Configure Settings** - Adjust performance and ticket types
3. **View Statistics** - See performance metrics
4. **Toggle Debug Mode** - Enable/disable detailed logging
5. **Exit** - Safely shutdown

## Configuration

### Performance Settings
- **Checks per minute**: How fast to check for tickets
- **Min/Max wait**: Wait time bounds between checks
- **Status updates**: How often to show progress

### Ticket Types
- **PRATO A** 🟢 - Field A tickets
- **PRATO B** 🔵 - Field B tickets  
- **SETTORE** 🟡 - Sector/Tribune tickets

### Browser Settings
- **Count**: 1-5 concurrent browsers
- **Positioning**: Automatic window placement
- **Session timeout**: Auto-refresh interval

## Troubleshooting

### If You See "Block Detected" Repeatedly
1. Check if you're actually blocked by looking at the browser
2. If not blocked, the site may have changed - enable debug mode
3. Reduce check frequency if getting real blocks

### If Tickets Aren't Being Detected
1. Enable debug mode from menu
2. Look for "Found X ticket elements" messages
3. Verify you're on the correct page
4. Check if ticket selector has changed

### Chrome Issues
```bash
# Version mismatch
python3 fix_chromedriver.py

# Stuck processes
python3 cleanup_chrome.py
```

## How It Works

### Ticket Detection Flow
1. Checks for tickets using `div[data-qa='ticketToBuy']` selector
2. Extracts ticket info (price, location, type)
3. Generates unique hash to avoid duplicates
4. Logs new tickets with color coding
5. Attempts purchase if type matches selection

### Purchase Flow
1. Scrolls ticket into view
2. Clicks ticket element
3. Waits for purchase button
4. Clicks purchase button
5. Takes screenshot
6. Logs success

### Block Detection (Fixed)
Only considers it blocked if:
- URL contains: 404, error, blocked
- Title contains: 404, error, non trovata
- Page has 404 but NOT "non sono state trovate"

## Performance Tips

### For Maximum Speed
- Use 2-3 browsers
- Set to Balanced or Aggressive mode
- Ensure good internet connection
- Close unnecessary programs

### For Stability
- Use Conservative mode
- Single browser
- Monitor for blocks
- Increase gradually

## Important Notes

1. **Credentials**: Store in `.env` file (never commit)
2. **Proxy**: Configure in `.env` if needed
3. **Target URL**: Set in environment or use default
4. **Screenshots**: Saved to `screenshots/` folder

## Statistics Tracking

The bot tracks:
- Total checks performed
- Unique tickets found
- Successful purchases
- Blocks encountered
- Session history

Statistics are saved to `fansale_stats_fixed.json`

## Best Practices

1. **Start Conservative**: Begin with lower rates
2. **Monitor Actively**: Watch first few minutes
3. **Adjust Gradually**: Increase speed if no blocks
4. **Use Debug Mode**: When troubleshooting
5. **Check Browsers**: Ensure they're on correct page

## Version Comparison

### Original (`fansale_no_login.py`)
- Fixed 650 checks/min
- Basic logging
- Working but aggressive

### Improved (`fansale_no_login_improved.py`)
- Configurable performance
- Enhanced logging
- Had false block detection issue

### Fixed (`fansale_no_login_fixed.py`)
- All improvements retained
- Block detection fixed
- Popup prevention added
- Debug mode included
- Fast purchasing ensured

## License

This bot is for educational purposes. Users are responsible for compliance with FanSale.it terms of service and local laws regarding automated purchasing systems.
