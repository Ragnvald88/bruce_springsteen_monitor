# StealthMaster - FanSale Bot V6

## Overview

StealthMaster is an advanced ticket hunting bot for FanSale.it, designed to monitor and automatically purchase concert tickets. Version 6 represents a complete architectural overhaul with significant performance improvements and enhanced features.

## Key Features

### 🚀 Performance
- **Ultra-fast checking**: 150-300 checks/minute per browser (3-5x faster than v5)
- **Real-time detection**: MutationObserver for instant ticket discovery
- **DOM caching**: Reduces redundant queries by 90%
- **Smart refresh**: Adaptive timing based on ticket discovery rate

### 📊 Enhanced Logging & Statistics
- **Category separation**: Individual loggers for Prato A, Prato B, and Settore
- **Color-coded output**: Visual differentiation for each ticket type
- **Live dashboard**: Real-time statistics with per-category breakdown
- **Performance metrics**: Track response times and success rates by category

### 🛡️ Anti-Detection
- **Human simulation**: Natural mouse movements and scrolling patterns
- **Behavioral variety**: Reading pauses and interaction variations
- **Enhanced stealth**: Advanced browser fingerprinting protection
- **Smart timing**: Adaptive delays based on activity patterns

### 🎯 Smart Features
- **Ticket scoring**: Prioritizes tickets by location, price, and category
- **Browser coordination**: Prevents duplicate purchases across browsers
- **Advanced filtering**: Set price limits, preferred sections, and minimum scores
- **Priority purchasing**: Automatically selects best tickets based on score

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/stealthmaster.git
cd stealthmaster

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your FanSale URL
# FANSALE_URL=https://www.fansale.it/fansale/tickets/...
# TWOCAPTCHA_API_KEY=your_api_key_here (optional)
```

## Quick Start

```bash
# Run the bot
python fansale_v6.py
```

## Configuration

### Basic Settings
- `browsers_count`: Number of parallel browsers (1-8)
- `max_tickets`: Maximum tickets to purchase (1-4)
- `min_wait` / `max_wait`: Check frequency control

### V6 Advanced Settings
- `use_mutation_observer`: Real-time DOM monitoring
- `enable_mouse_simulation`: Human behavior simulation
- `smart_refresh`: Adaptive page refresh
- `ticket_priority_scoring`: Score-based prioritization
- `browser_coordination`: Duplicate prevention
- `advanced_filtering`: Price/section filters

## Usage

1. **Start the bot**: `python fansale_v6.py`
2. **Configure settings**: Choose browsers, tickets, and categories
3. **Set filters** (optional): Price limits, preferred sections
4. **Start hunting**: Press Enter to begin
5. **Monitor progress**: Watch the live dashboard

## Output Examples

### Category-Specific Logging
```
12:34:56 🎫[PRATO A] 🚨 ALERT: NEW TICKET FOUND by Hunter 1!
12:34:56 🎫[PRATO A] └─ Section: Prato Gold A | Price: €95.00 | Score: 125.0
12:34:56 🎫[PRATO A] ────────────────────────────────────────────────────────────

12:34:57 🎫[SETTORE] 🚨 ALERT: NEW TICKET FOUND by Hunter 2!
12:34:57 🎫[SETTORE] └─ Row: 5 | Seat: 15 | Ring: 2 Anello Verde | Price: €120.00 | Score: 118.0
12:34:57 🎫[SETTORE] ────────────────────────────────────────────────────────────
```

### Live Dashboard
```
================================================================================
                    🎫 FANSALE BOT V6 - LIVE DASHBOARD
================================================================================

⏱️  Runtime: 00:15:32
🎯 Tickets Secured: 1/2

📊 CATEGORY BREAKDOWN:
------------------------------------------------------------
Category     Checks      Found   Purchased  Avg Response
------------------------------------------------------------
Prato A         1,234         3           1        0.125s
Prato B           987         2           0        0.132s
Settore         1,456         5           0        0.118s
Other             234         1           0        0.141s

⚡ PERFORMANCE:
------------------------------------------------------------
Browser 1: 156.3 checks/min (avg: 0.384s)
Browser 2: 162.7 checks/min (avg: 0.369s)

📈 BEST HUNTING HOURS:
   14:00 - 12 tickets found
   15:00 - 8 tickets found
   20:00 - 7 tickets found
```

## File Structure

```
stealthmaster/
├── fansale_v6.py           # Main bot script
├── bot_config_v6.json      # Configuration file
├── .env                    # Environment variables
├── MIGRATION_V6.md         # Migration guide from v5
├── V5_VS_V6_COMPARISON.md  # Detailed comparison
└── logs/
    ├── fansale_v6_prato_a.log
    ├── fansale_v6_prato_b.log
    ├── fansale_v6_settore.log
    └── fansale_v6_system.log
```

## Advanced Features

### Ticket Scoring Algorithm
Tickets are scored based on:
- **Category**: Prato A (30pts) > Prato B (25pts) > Settore (20pts)
- **Price**: Lower prices score higher
- **Location**: For Settore - lower rows and central seats score higher
- **Custom weights**: Configurable via advanced settings

### Human Simulation
- **Mouse movements**: Bezier curves for natural paths
- **Scrolling**: Random viewport interactions
- **Reading pauses**: Gaussian-distributed delays
- **Action variety**: Prevents pattern detection

### Performance Optimizations
- **DOM Caching**: Static elements cached for 30 seconds
- **Mutation Observer**: Instant detection without polling
- **Batch processing**: Efficient handling of multiple tickets
- **Smart delays**: Reduced wait times when tickets are found

## Troubleshooting

### Common Issues

1. **"Images not loading" error**
   - This is usually a false positive
   - Images are verified on the actual site now

2. **High CPU usage**
   - Reduce number of browsers
   - Increase wait times
   - Disable mouse simulation

3. **CAPTCHA issues**
   - Ensure 2captcha API key is set
   - Browser 1 checks every 5 minutes
   - Manual solving fallback available

### Performance Tuning

For maximum speed:
```json
{
  "min_wait": 0.1,
  "max_wait": 0.5,
  "dom_cache_duration": 60,
  "use_mutation_observer": true
}
```

For stealth:
```json
{
  "min_wait": 0.5,
  "max_wait": 2.0,
  "enable_mouse_simulation": true,
  "smart_refresh": true
}
```

## Contributing

Feel free to submit issues and enhancement requests!

## Legal Notice

This bot is for educational purposes only. Users are responsible for compliance with website terms of service and local laws.

## Changelog

### V6.0.0 (2025-01-06)
- Complete architectural overhaul
- Separated category logging
- 3-5x performance improvement
- Real-time detection with MutationObserver
- Human behavior simulation
- Advanced filtering and scoring
- Live statistics dashboard
- Browser coordination
- Enhanced anti-detection

### V5.0.0
- Initial stable release
- Multi-browser support
- CAPTCHA handling
- Basic statistics
