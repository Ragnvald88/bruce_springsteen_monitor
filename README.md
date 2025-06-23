# FanSale Bot - Enhanced Hunter-Buyer Edition 🎯

## 🚀 Lightning-Fast Ticket Sniping

The ultimate FanSale.it ticket bot with blazing-fast purchase execution and aggressive checking rates.

```bash
python3 fansale.py
```

## ⚡ Key Features

- **Hunter-Buyer Architecture**: Each browser hunts AND buys instantly
- **Aggressive Checking**: 20-60 checks/minute total
- **Lightning Purchase**: <1 second from detection to buy click
- **Pattern Variation**: Automatic switching between burst/normal/slow/random
- **Advanced Stealth**: Comprehensive anti-detection measures
- **Manual Login**: More secure than automation

## 🏃 Quick Start

1. **Setup Environment**:
```bash
# Create .env file with your credentials
FANSALE_EMAIL=your@email.com
FANSALE_PASSWORD=yourpassword
FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554

# Optional proxy settings
IPROYAL_USERNAME=your_username
IPROYAL_PASSWORD=your_password
IPROYAL_HOSTNAME=geo.iproyal.com
IPROYAL_PORT=12321
```

2. **Install Dependencies**:
```bash
pip3 install -r requirements.txt
```

3. **Run the Bot**:
```bash
python3 fansale.py
```

## 🎮 Configuration Options

The bot will prompt you for:
- **Number of Browsers** (1-5, recommended 2-3)
- **Proxy Usage** (recommended for multiple browsers)
- **Ultra-Lite Mode** (blocks images/CSS for speed)
- **Stealth Enhancements** (advanced anti-detection)

## 📊 Performance by Browser Count

| Browsers | Checks/Browser/Min | Total Checks/Min | Risk Level |
|----------|-------------------|------------------|------------|
| 1 | 15-20 | 15-20 | Low |
| 2 | 12-15 | 25-30 | Low-Medium |
| 3 | 10-12 | 30-36 | Medium |
| 4 | 8-10 | 32-40 | Medium-High |
| 5 | 8-10 | 40-50 | High |

## 🏗️ How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Hunter-Buyer 1  │     │ Hunter-Buyer 2  │     │ Hunter-Buyer 3  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ ✓ Hunts tickets │     │ ✓ Hunts tickets │     │ ✓ Hunts tickets │
│ ✓ Buys instant  │     │ ✓ Buys instant  │     │ ✓ Buys instant  │
│ ✓ Independent   │     │ ✓ Independent   │     │ ✓ Independent   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                │
                        [Purchase Lock]
                                │
                    First to find = First to buy!
```

## 🛡️ Anti-Detection Features

- **Pattern Variation**: Switches between burst/normal/slow/random patterns
- **Timing Randomization**: No predictable refresh intervals
- **Human Behaviors**: Random mouse movements and scrolling
- **Viewport Changes**: Random window size variations
- **Multiple Refresh Methods**: Alternates between JS and normal refresh
- **Browser Fingerprinting Protection**: Comprehensive stealth JavaScript

## ⚠️ Important Warnings

### Detection Risks
- Multiple logged-in sessions increase detection risk
- Aggressive checking rates (20-60/min) are similar to professional bots
- Always use proxies for multiple browsers
- Monitor for rate limiting or blocks

### Best Practices
1. **Start Small**: Test with 1-2 browsers first
2. **Use Proxies**: Italian proxies recommended for FanSale.it
3. **Take Breaks**: Don't run continuously for hours
4. **Monitor Activity**: Watch for captchas or blocks

## 🔧 Troubleshooting

**Browser won't start?**
- Check Chrome/Chromium is installed
- Clear browser_profiles/ directory
- Reduce number of browsers

**Login fails?**
- Verify credentials in .env
- Check for captcha requirements
- Try one browser first

**Getting blocked?**
- Reduce number of browsers
- Enable proxy
- Increase refresh intervals
- Take longer breaks

## 📁 Project Structure

```
stealthmaster/
├── fansale.py                    # Main entry point
├── fansale_hunter_buyer.py       # Core implementation
├── utilities/
│   ├── stealth_improvements.py   # Anti-detection measures
│   └── speed_optimizations.py    # Performance enhancements
├── browser_profiles/             # Persistent browser data
├── .env                          # Your credentials (create this)
└── requirements.txt              # Python dependencies
```

## 🚀 Advanced Usage

### Compare Implementations
```bash
python3 compare_implementations.py
```

### Manual Timing Adjustment
Edit `calculate_smart_refresh_timing()` in `fansale_hunter_buyer.py` to customize rates.

### Stealth Testing
The bot automatically tests stealth measures and shows a score (0-100).

## 📈 Future Enhancements

- [ ] AI-powered ticket detection
- [ ] Distributed multi-machine support
- [ ] Advanced analytics dashboard
- [ ] Auto-recovery on failures
- [ ] Mobile app notifications

---

**⚡ Remember**: Speed is everything in ticket sniping. First to find = First to buy!

*Version 2.0 - Enhanced Hunter-Buyer Edition*
*Last Updated: June 2025*
