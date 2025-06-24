# StealthMaster Project - Claude AI Guide

## 🎯 Project Overview
StealthMaster is an advanced ticket purchasing bot for FanSale.it that automatically detects and purchases concert/event tickets without requiring login.

## 🚀 Key Features
- **No Login Required**: Tickets can be reserved without authentication
- **Ticket Type Categorization**: Tracks Prato A, Prato B, and Settore tickets separately
- **Selective Hunting**: Choose which ticket types to hunt for
- **Duplicate Detection**: Avoids logging the same ticket multiple times
- **Persistent Statistics**: Continues counting from previous sessions
- **Multi-Monitor Support**: Browsers positioned across multiple monitors
- **Anti-Detection**: Uses undetected-chromedriver with stealth enhancements
- **Beautiful Logging**: Color-coded ticket types with full details

## 📁 Project Structure
```
stealthmaster/
├── fansale_no_login.py    # Main enhanced bot (NO LOGIN) - RECOMMENDED
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
4. **Logs**: Color-coded output shows ticket categories clearly
5. **404 Blocks**: Bot automatically clears browser data to bypass

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

## 📊 Statistics Tracked
- Total checks across all sessions
- Unique tickets found by type
- Successful purchases
- 404 blocks encountered
- Total runtime hours

## 🚨 Important Notes
- No login required for ticket reservation
- Duplicate tickets are tracked but not re-logged
- Statistics persist between restarts
- Screenshots saved on successful checkout
- Session refresh every 15 minutes prevents blocks
- Logs show [HUNTING] for selected types, [TRACKING] for others

## 🐛 Troubleshooting
1. **404 Errors**: Bot auto-clears browser data
2. **Session Dies**: Restart the bot
3. **No Tickets Found**: Check if event has tickets available
4. **Stats Reset**: Delete `fansale_stats.json` to start fresh

## 🎯 Performance Expectations
- 1 browser: ~20-24 checks/minute
- 2 browsers: ~40-48 checks/minute
- 3+ browsers: Diminishing returns, higher detection risk

## 🔍 How It Works
1. Creates stealth browsers with anti-detection
2. Navigates to event page (no login)
3. Monitors for ticket availability
4. Categorizes tickets (Prato A/B, Settore, Other)
5. Tracks unique tickets to avoid duplicates
6. Logs full ticket details on first discovery
7. Attempts purchase only for selected categories
8. Saves persistent statistics

## 🎨 Terminal Output
- 🟢 **Green**: Prato A tickets
- 🔵 **Blue**: Prato B tickets
- 🟡 **Yellow**: Settore tickets
- 🔷 **Cyan**: Other tickets
- [HUNTING] vs [TRACKING] indicators
- Stats dashboard every 60 seconds

## 📈 Future Enhancements
- [ ] Email/SMS notifications
- [ ] Web dashboard for stats
- [ ] Proxy rotation support
- [ ] Advanced filtering rules
- [ ] Price range filters