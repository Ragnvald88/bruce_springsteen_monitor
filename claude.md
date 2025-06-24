# StealthMaster Project - Claude AI Guide

## 🔴 IMPORTANT RULES FOR CLAUDE AI
1. **NEVER CHANGE FILENAMES** - All existing filenames must remain exactly as they are
2. Do not rename, move, or suggest renaming any files in the project
3. Create new files with new names instead of renaming existing ones

## 🎯 Project Overview
StealthMaster is an enterprise-grade ticket purchasing bot for FanSale.it that automatically detects and purchases concert/event tickets without requiring login.

## 🚀 Key Features
- **No Login Required**: Tickets can be reserved without authentication
- **Advanced Ticket Categorization**: Tracks Prato A, Prato B, and Settore tickets separately
- **Selective Hunting**: Choose which ticket types to hunt for with "All Prato" option
- **Duplicate Detection**: Avoids logging the same ticket multiple times
- **Persistent Statistics**: Thread-safe stats that persist across restarts
- **Multi-Monitor Support**: Smart browser positioning across multiple monitors
- **Anti-Detection**: Uses undetected-chromedriver with stealth enhancements
- **Health Monitoring**: Tracks browser and system health
- **Notification System**: High-priority alerts for ticket discoveries
- **Advanced Retry Logic**: Sophisticated retry decorator with exponential backoff
- **Configuration Support**: JSON-based configuration with defaults

## 📁 Project Structure
```
stealthmaster/
├── fansale_no_login.py    # Main enhanced bot (NO LOGIN) - ENTERPRISE EDITION
├── fansale.py             # Original version with login support
├── fansale_stealth.py     # Streamlined 350-line version
├── utilities/             # Enhancement modules
│   ├── stealth_enhancements.py
│   ├── speed_optimizer.py
│   └── session_manager.py
├── browser_profiles/      # Persistent browser data
├── screenshots/           # Checkout screenshots
├── .env                   # Credentials and config
├── fansale_stats.json     # Persistent statistics
├── bot_config.json        # Bot configuration (auto-created)
└── requirements.txt       # Dependencies
```

## 🎫 Italian Venue Terminology
- **Prato** (A/B/Gold): Standing lawn areas
- **Parterre**: Floor/pit sections
- **Tribuna**: Seated tribune/stands
- **Settore**: Numbered sectors
- **Curva**: Curved stadium sections
- **Distinti**: Distinguished sections

## 🛠️ Setup Instructions
```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env file
FANSALE_TARGET_URL="https://www.fansale.it/fansale/tickets/..."

# Run the enhanced bot
python fansale_no_login.py
```

## 💡 Usage Tips
1. **Browser Count**: Use 2-3 browsers for optimal performance
2. **Multi-Monitor**: Browsers auto-position across monitors
3. **Statistics**: Check `fansale_stats.json` for historical data
4. **Configuration**: Edit `bot_config.json` for persistent settings
5. **404 Blocks**: Bot automatically clears browser data to bypass
6. **Health Monitoring**: System resources tracked automatically

## 🎯 Ticket Type Selection
During configuration, you can select which ticket types to hunt:
- **1**: Prato A only
- **2**: Prato B only
- **3**: All Prato tickets (A + B) ⭐
- **4**: Settore only
- **5**: Other/Unknown tickets
- **6**: ALL ticket types

Examples:
- Enter "3" to hunt all Prato tickets
- Enter "1,4" to hunt Prato A and Settore
- Enter "6" or press Enter to hunt everything
- Default: All Prato tickets (A + B)

## 📊 Enhanced Features

### 🔄 Retry Decorator
Automatic retry with exponential backoff for failed operations:
```python
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def critical_operation():
    # Automatically retries on failure
```

### 🧵 Thread-Safe Statistics
All statistics operations are thread-safe with atomic writes:
- Prevents data corruption
- Backup file creation before save
- Automatic recovery on failure

### 🏥 Health Monitoring
- Browser responsiveness checks
- Memory usage tracking
- System resource monitoring
- Automatic recovery on unhealthy state

### 📢 Notification System
- High-priority alerts for hunting ticket types
- Visual alerts in terminal
- Notification queue for history
- Extensible for email/SMS

### ⚙️ Configuration File
`bot_config.json` (auto-created with defaults):
```json
{
  "browsers_count": 2,
  "max_tickets": 2,
  "refresh_interval": 30,
  "session_timeout": 900,
  "min_wait": 2.0,
  "max_wait": 4.0,
  "retry_attempts": 3,
  "retry_delay": 1.0
}
```

## 📊 Statistics Tracked
- Total checks across all sessions
- Unique tickets found by type
- Successful purchases
- 404 blocks encountered
- Total runtime hours
- Browser health metrics
- System resource usage

## 🚨 Important Notes
- No login required for ticket reservation
- Duplicate tickets tracked but not re-logged
- All sleep times randomized for anti-detection
- No bare except clauses - proper error handling
- Thread-safe operations throughout
- Atomic file writes for data integrity

## 🐛 Troubleshooting
1. **404 Errors**: Bot auto-clears browser data
2. **Session Dies**: Restart the bot
3. **No Tickets Found**: Check if event has tickets available
4. **Stats Reset**: Delete `fansale_stats.json` to start fresh
5. **Config Reset**: Delete `bot_config.json` for defaults

## 🎯 Performance Expectations
- 1 browser: ~20-24 checks/minute
- 2 browsers: ~40-48 checks/minute
- 3+ browsers: Diminishing returns, higher detection risk
- Memory usage: ~250MB per browser
- CPU usage: 5-10% idle, 20-30% active

## 🔍 Technical Improvements
1. **Error Handling**: All exceptions properly caught and logged
2. **Sleep Randomization**: All delays use random ranges
3. **Retry Logic**: Critical operations retry automatically
4. **Thread Safety**: All shared resources properly locked
5. **Resource Management**: Proper cleanup in finally blocks
6. **Type Safety**: Enhanced with type hints throughout

## 🎨 Terminal Output
- 🟢 **Green**: Prato A tickets
- 🔵 **Blue**: Prato B tickets
- 🟡 **Yellow**: Settore tickets
- 🔷 **Cyan**: Other tickets
- 🚨 **Red Alert**: High-priority notifications
- [HUNTING] vs [TRACKING] indicators
- Stats dashboard every 60 seconds
- Health metrics in dashboard

## 📈 Enterprise Features
- **Graceful Shutdown**: Proper cleanup on exit
- **Configuration Management**: Persistent settings
- **Health Checks**: Automatic browser health monitoring
- **Performance Metrics**: Detailed performance tracking
- **Error Recovery**: Automatic recovery from failures
- **Logging Levels**: Debug, Info, Warning, Error
- **Resource Limits**: Configurable resource constraints

## 🔧 Advanced Configuration
Edit `bot_config.json` for advanced settings:
- `browsers_count`: Number of concurrent browsers
- `max_tickets`: Maximum tickets to purchase
- `refresh_interval`: Page refresh interval (seconds)
- `session_timeout`: Session refresh timeout (seconds)
- `min_wait`: Minimum wait between actions
- `max_wait`: Maximum wait between actions
- `retry_attempts`: Number of retry attempts
- `retry_delay`: Initial retry delay (seconds)

## 🎯 Best Practices
1. Start with 2 browsers for optimal performance
2. Use manual ticket type selection for focused hunting
3. Monitor health metrics in the dashboard
4. Check notification queue for missed alerts
5. Review logs for debugging issues
6. Adjust configuration based on success rate

## 🚀 Performance Optimization
- Smart refresh strategy (partial vs full)
- Efficient element detection
- Minimal DOM interactions
- Optimized memory usage
- Resource pooling
- Connection reuse

The bot is now enterprise-ready with professional-grade error handling, monitoring, and configuration management! 🎉