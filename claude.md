# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FanSale ticket monitoring and automated reservation bot (fansale.py) that operates without login requirements. The bot uses multiple concurrent browsers to maximize ticket detection speed and automatically reserves tickets matching user-defined criteria.

## Core Architecture

### Speed-Critical Ticket Detection Flow

The bot's primary optimization is its parallel detection and instant reservation system:

1. **Multi-Browser Hunting** (hunt_tickets method, line 674):
   - Each browser runs in its own thread for parallel monitoring
   - Browsers check for tickets using CSS selector: `div[data-qa='ticketToBuy']`
   - Check interval: 2.5-3.5 seconds with full page refresh every 30 seconds
   - Session refresh every 15 minutes to prevent detection

2. **Duplicate Detection System** (lines 720-726):
   - MD5 hashing of ticket text (stripped of timestamps) prevents re-processing
   - Only new tickets trigger the purchase flow, dramatically reducing overhead
   - Hash generation removes dynamic elements for consistent identification

3. **Instant Purchase Trigger** (lines 741-751):
   - Purchase attempt happens immediately upon detecting matching ticket type
   - Uses thread-safe `purchase_lock` to prevent race conditions
   - No intermediate steps - direct ticket click → buy button click

### Critical Speed Optimizations

```python
# Key optimization points in purchase_ticket (line 803):
1. JavaScript click instead of Selenium click (faster, more reliable)
2. Minimal wait time: 0.8-1.2 seconds between actions
3. Multiple buy button selectors tried in sequence
4. 2-second timeout for buy button detection (WebDriverWait)
```

### Thread Architecture

- **Main Thread**: User interface, configuration, statistics monitoring
- **Hunter Threads**: One per browser, continuously scanning for tickets
- **Synchronization**: 
  - `purchase_lock` (threading.Lock) ensures single purchase at a time
  - `shutdown_event` (threading.Event) for graceful shutdown
  - `StatsManager` with internal lock for thread-safe statistics

### Anti-Detection Mechanisms

1. **Browser Creation** (create_browser, line 476):
   - Undetected ChromeDriver with stealth JavaScript injection
   - Persistent browser profiles to maintain cookies/storage
   - Multi-version fallback system (Chrome 137, auto-detect, 138)

2. **Block Recovery** (lines 694-699):
   - Automatic 404 detection and browser data clearing
   - Session refresh without restart
   - Statistics tracking of blocks encountered

3. **Human-like Behavior**:
   - Random timing variations (2.5-3.5s between checks)
   - Browser window positioning for multi-monitor setups
   - Staggered browser startup

## Key Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python3 fansale.py

# Fix Python 3.13 compatibility issues
pip install --force-reinstall setuptools
```

## Configuration System

### Environment Variables (.env)
- `FANSALE_TARGET_URL`: Event page to monitor
- No login credentials needed (bot operates without authentication)

### Bot Configuration (bot_config.json)
```json
{
  "browsers_count": 2,      # Number of parallel browsers
  "max_tickets": 2,         # Stop after securing this many
  "refresh_interval": 30,   # Full page refresh interval
  "session_timeout": 900    # Session refresh interval (15 min)
}
```
these settings can be changed in the menu when the script opens. 

### Runtime Configuration
- User selects ticket types to hunt (Prato A, B, Settore, etc.)
- Dynamic browser count selection (1-8 browsers)
- Real-time statistics display

## Performance Metrics

Based on fansale_stats.json analysis:
- Average check rate: ~200-250 checks/minute (with 2 browsers)
- Unique ticket detection: ~1% of total tickets found
- Block recovery: Automatic with ~5 blocks per 10,000 checks

## Critical Files & Data Flow

1. **fansale.py**: Main bot implementation
2. **fansale_stats.json**: Persistent statistics (thread-safe updates)
3. **browser_profiles/**: Chrome profiles for session persistence
4. **screenshots/**: Automatic capture on successful reservation

## Code Patterns for Maximum Speed

When modifying the ticket detection/purchase flow:

1. **Minimize DOM interactions**: Use JavaScript execution over Selenium methods
2. **Parallel operations**: Each browser operates independently
3. **Early filtering**: Hash-based duplicate detection prevents redundant processing
4. **Fail-fast purchasing**: Immediate attempt on detection, no queuing
5. **Thread safety**: Always use locks when accessing shared state

## Debugging & Monitoring

- Console output with color-coded ticket types
- Real-time statistics dashboard (every 60 seconds)
- Detailed logging to fansale_bot.log
- Screenshot capture on successful reservation