# CLAUDE.md - FanSale Ultimate Bot

This file provides guidance to Claude Code when working with the FanSale Ultimate Bot in this repository.

## 🎯 Project Overview

**FanSale Ultimate Bot** is a high-performance, automated ticket reservation system for FanSale.it. It combines speed with a user-friendly interface, real-time statistics, and persistent settings.

### Core Philosophy
- **Speed with visibility** - Fast hunting with real-time feedback
- **User-friendly** - Menu system and persistent settings
- **Reliable** - Robust error handling and recovery

## 🏃 Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_ultimate.txt

# Configure
cp .env.example .env
# Edit .env with your FanSale URL

# Run
python3 fansale_ultimate.py
```

## 🏗️ Architecture

The bot is contained in `fansale_ultimate.py` with these key components:

#### Main Classes
- **FanSaleUltimate**: Core bot logic and orchestration
- **SettingsManager**: Persistent configuration handling
- **StatsTracker**: Real-time statistics tracking
- **TerminalUI**: Menu system and display management

#### Key Methods
```python
FanSaleUltimate/
├── main()                  # Menu loop and application control
├── configure_settings()    # Interactive settings configuration
├── run_bot()              # Bot execution with live stats
├── create_browser()       # Undetected Chrome with stealth
├── hunt_tickets()         # Main hunting loop per browser
├── attempt_purchase()     # Click ticket & buy button
├── detect_captcha()       # CAPTCHA detection
├── solve_captcha()        # Auto (2captcha) or manual
└── display_live_stats()   # Real-time statistics display
```

## ⚡ Performance Metrics

Based on validated benchmarks:
- **Ticket Categorization**: 1,180,000+ per second
- **Hash Generation**: 800,000+ per second
- **Duplicate Detection**: 10,000,000+ lookups per second
- **Decision Latency**: < 0.01ms
- **Expected Check Rate**: 60-300 checks/minute per browser

## 🎯 Critical Flows

### 1. Ticket Detection Flow
```python
# Ultra-fast checking loop (0.3-1.0s intervals)
while hunting:
    dismiss_popups()      # Every 10s
    find_tickets()        # Multiple selectors
    check_duplicates()    # O(1) set lookup
    categorize()          # Instant classification
    attempt_purchase()    # If matching criteria
    refresh_page()        # Every 15±3s
```

### 2. Purchase Flow
```python
1. Click ticket element (3 methods)
2. Wait for buy button (multiple selectors)
3. Click buy button
4. Handle CAPTCHA if present
5. Take screenshot as proof
```

### 3. Selectors (Priority Order)

**Ticket Detection:**
```css
div[data-qa='ticketToBuy']              /* Primary */
a.offer-list-item                       /* Secondary */
div[class*='ticket'][class*='available'] /* Fallback */
```

**Buy Button:**
```css
button[data-qa='buyNowButton']          /* FanSale specific */
//button[contains(text(), 'Acquista')]   /* Italian */
button[class*='buy']                    /* Generic */
```

## 🔧 Configuration

### Environment Variables
```bash
FANSALE_TARGET_URL=https://www.fansale.it/tickets/all/...
TWOCAPTCHA_API_KEY=your_key_here  # Optional
```

### Runtime Options
- **Browsers**: 1-8 concurrent instances
- **Max Tickets**: Stop after securing N tickets
- **Ticket Types**: Prato A, Prato B, Settore, Other, All

## 🛡️ Anti-Detection Features

1. **Undetected ChromeDriver** with version fallback
2. **Stealth JavaScript** injection
3. **Natural timing** with random delays
4. **Italian locale** settings
5. **Realistic window** positioning

## 🤖 CAPTCHA Handling

### Automatic (2captcha)
- Detects reCAPTCHA presence
- Extracts site key
- Requests solution via API
- Injects token via JavaScript

### Manual Fallback
- Audio + visual alert
- 2-minute timeout
- 5-minute grace period after solving

## 📊 Logging System

Simple, colored console output:
- 🔵 **INFO** (Cyan): General information
- 🟢 **SUCCESS** (Green): Positive outcomes
- 🟡 **WARNING** (Yellow): Important notices
- 🔴 **ERROR** (Red): Problems
- 🟣 **ALERT** (Magenta): Critical events + sound

## 🚀 Usage Tips

### For Maximum Success
1. **Use 2-4 browsers** for optimal performance
2. **Set specific ticket types** to reduce noise
3. **Have 2captcha credits** or be ready to solve manually
4. **Run on stable connection** with low latency
5. **Position browsers** across multiple monitors

### Common Issues
- **Chrome version mismatch**: Bot tries multiple versions automatically
- **Session dies**: Thread exits gracefully, others continue
- **CAPTCHA appears**: Handled automatically or with alert

## 📝 Development Guidelines

### When Modifying Code
1. **Keep it simple** - No unnecessary abstractions
2. **Keep it fast** - Profile any changes
3. **Keep it working** - Test with real pages
4. **Keep it clean** - One purpose per method

### What NOT to Add
- ❌ Terminal UI dashboards
- ❌ Database/file persistence  
- ❌ Complex configuration systems
- ❌ Multiple classes/files
- ❌ Non-essential features

### What TO Consider
- ✅ Faster ticket detection methods
- ✅ Additional selector fallbacks
- ✅ Better CAPTCHA handling
- ✅ Platform compatibility fixes

## 🧪 Testing

```bash
# Run performance benchmarks
python3 test_performance.py

# Expected output:
# ✅ Ticket categorization: >20,000/second
# ✅ Hash generation: >30,000/second
# ✅ Set lookups: >1,000,000/second
# ✅ Thread safety: Verified
# ✅ Decision latency: <10ms
# ✅ Multi-browser scaling: Linear
```

## 🚀 Features

### User Interface
- **Main Menu**: Run Bot, Settings, Statistics, Help
- **Settings Menu**: Configure all options with persistence
- **Live Statistics**: Real-time display during hunting
  - Runtime counter
  - Checks per minute
  - Tickets found by category
  - Active browser status

### Persistent Settings (`bot_settings.json`)
- Number of browsers (1-8)
- Max tickets to secure
- Ticket type filtering
- Check speed (min/max wait)
- Refresh interval
- Proxy configuration
- Sound alerts toggle
- Auto screenshot toggle

### Enhanced Logging
- **Real-time ticket notifications** when found
- **Color-coded log levels** for easy reading
- **Per-browser tracking** for multi-instance clarity
- **Statistics tracking** across sessions

### Additional Features
- **Proxy Support**: Optional proxy configuration
- **Sound Alerts**: Audio notifications for important events
- **Historical Stats**: Track performance across runs
- **Graceful Shutdown**: Ctrl+C handling with cleanup

## 🎯 Remember

This bot has ONE job: **Get tickets before others do**.

Every feature is designed to support that goal while providing visibility and control.

---

**Last Updated**: December 2024  
**Main Script**: `fansale_ultimate.py`