# FanSale Ticket Hunter Bot - Enhanced Version

## Overview
The FanSale Ticket Hunter Bot is an automated ticket purchasing system for FanSale.it, designed to monitor and secure tickets for concerts and events. This enhanced version includes improved logging, configurable performance settings, and a better user interface.

## Key Improvements

### 1. **Configurable Check Frequency**
- **Previous**: Fixed at 650 checks/minute (way too aggressive)
- **Now**: Configurable from 30-600 checks/minute with presets:
  - Conservative: 60 checks/min (safest)
  - Balanced: 120 checks/min (recommended)
  - Aggressive: 240 checks/min (faster but riskier)
  - Custom: User-defined settings

### 2. **Enhanced Logging System**
- **Improved formatting**: Cleaner, more readable logs with proper timestamps
- **Configurable log levels**: ERROR, WARNING, INFO, DEBUG
- **Adjustable status update frequency**: Default every 50 checks
- **Better visual indicators**: Speed icons (🚀/✅/⚠️) based on performance
- **Detailed logging toggle**: For debugging without cluttering normal operation

### 3. **Improved Menu System**
- **Main Menu**: Shows current configuration summary
- **Configuration Menu**: Organized settings by category
- **Performance Settings**: Easy preset selection or custom configuration
- **Real-time Statistics**: Enhanced dashboard with session history
- **Browser Configuration**: Support for 1-5 concurrent browsers

### 4. **Performance Optimizations**
- **Smart wait time calculation**: Based on desired checks/minute
- **Health monitoring**: Tracks errors and performance degradation
- **Better error handling**: Categorized errors with appropriate responses
- **Session management**: Configurable timeout (5-60 minutes)

### 5. **User Experience Enhancements**
- **Desktop notifications**: For ticket discoveries (macOS/Linux)
- **Color-coded output**: Better visual distinction for different ticket types
- **Progress indicators**: Cleaner status updates without spam
- **Session summaries**: Detailed statistics after each run

## Configuration Options

### Performance Settings
```json
{
  "checks_per_minute": 120,      // Target checking rate
  "min_wait": 0.4,               // Minimum wait between checks
  "max_wait": 0.6,               // Maximum wait between checks
  "status_update_interval": 50   // Update status every N checks
}
```

### Logging Settings
```json
{
  "log_level": "INFO",           // ERROR, WARNING, INFO, DEBUG
  "detailed_logging": false      // Enable/disable verbose logging
}
```

### Bot Settings
```json
{
  "browsers_count": 2,           // Number of concurrent browsers (1-5)
  "max_tickets": 4,              // Maximum tickets to purchase
  "session_timeout": 900,        // Session refresh interval (seconds)
  "ticket_types_to_hunt": ["prato_b", "prato_a"]  // Target ticket types
}
```

## Usage

### Starting the Bot
```bash
python3 fansale_no_login_improved.py
```

### Menu Navigation
1. **Start Hunting**: Begin monitoring with current settings
2. **Configure Settings**: Access the configuration menu
3. **View Statistics**: See detailed performance metrics
4. **Reset Statistics**: Clear all historical data
5. **Exit**: Safely shutdown the bot

### Configuration Menu
- **Ticket Types**: Select which ticket categories to target
- **Performance**: Adjust checking frequency and timing
- **Browsers**: Set number of concurrent browsers
- **Logging**: Configure verbosity and update frequency
- **Max Tickets**: Set purchase limit
- **Session Timeout**: Configure refresh interval

## Recommended Settings

### For Stability (Low Risk)
- Browsers: 1-2
- Checks/minute: 60-120
- Session timeout: 15 minutes
- Log level: INFO

### For Speed (Higher Risk)
- Browsers: 3-4
- Checks/minute: 180-240
- Session timeout: 10 minutes
- Log level: WARNING (less verbose)

## Technical Details

### Architecture
- **Multi-threaded**: Each browser runs in its own thread
- **Thread-safe**: Purchase operations use locks to prevent conflicts
- **Async browser creation**: Parallel browser initialization
- **Health monitoring**: Tracks performance and errors per browser

### Anti-Detection Features
- Undetected ChromeDriver with stealth patches
- Random wait times within configured bounds
- Session refresh to avoid long-running detection
- Browser data clearing on block detection
- JavaScript injection to hide automation markers

### Error Handling
- **Network errors**: Automatic retry with backoff
- **Session errors**: Browser restart
- **Block detection**: Clear data and refresh
- **Timeout handling**: Progressive retry strategy

## Statistics Tracking

### Session Metrics
- Total checks performed
- Unique tickets discovered
- Successful purchases
- Blocks encountered
- Runtime duration

### Ticket Breakdown
- Prato A (Field A) - Green 🟢
- Prato B (Field B) - Blue 🔵
- Settore (Sector) - Yellow 🟡

### Historical Data
- Last 10 sessions stored
- All-time statistics
- Performance trends

## Troubleshooting

### Chrome Version Issues
```bash
python3 fix_chromedriver.py
```

### Stuck Chrome Processes
```bash
python3 cleanup_chrome.py
```

### Performance Issues
- Reduce number of browsers
- Lower checks per minute
- Increase wait times
- Check system resources

## Best Practices

1. **Start Conservative**: Begin with lower check rates and increase gradually
2. **Monitor Blocks**: If seeing blocks, reduce frequency immediately
3. **Use Multiple Browsers Wisely**: More isn't always better - find the sweet spot
4. **Regular Breaks**: Use session timeout to avoid continuous running
5. **Watch the Logs**: Pay attention to error rates and warnings

## Security Notes

- Never share your `.env` file with credentials
- Use VPN if concerned about IP blocking
- Monitor for unusual activity
- Keep ChromeDriver updated

## Future Enhancements

Potential improvements for future versions:
- Proxy rotation support
- Advanced captcha handling
- Email/SMS notifications
- Web dashboard interface
- Machine learning for optimal timing
- Database storage for analytics

## License

This bot is for educational purposes. Users are responsible for compliance with FanSale.it terms of service and local laws regarding automated purchasing systems.
