# StealthMaster - FanSale Ticket Bot (NO LOGIN REQUIRED) 🎫

A ticket purchasing bot for FanSale.it with anti-detection measures. **No login required!**

## Quick Start

1. **Setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file (only URL needed!)
FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/...
```

2. **Run**:
```bash
python fansale_no_login.py  # Recommended - no login required!
```

## Key Features

- 🤖 Anti-detection with undetected-chromedriver
- 🎯 Smart ticket filtering (Prato, Tribuna, etc.)
- 🔄 Automatic session refresh to avoid blocks
- 📊 Performance tracking and statistics
- 🖼️ Screenshot capture on successful checkout

## File Structure

```
fansale_no_login.py   # ← Main bot (no login required!)
fansale_stealth.py    # Previous streamlined version
fansale.py           # Original full-featured version
test_login.py        # Test login detection
claude.md            # Guide for Claude AI
CHANGELOG.md         # Version history & lessons
```

## Important Notes

- **No Login Required**: Tickets can be reserved without authentication!
- **404 Blocks**: Clear browser data if you get 404 errors after extended use
- **Max Browsers**: Use 1-2 browsers to avoid detection
- **Ticket Filtering**: Specify sections like "Prato A", "Tribuna", etc.

## Configuration

The bot will prompt you for:
- Number of browsers (1-3, recommend 1-2)
- Proxy usage (optional)
- Ticket filters (optional)
- Max tickets to purchase (1-4)

## Troubleshooting

See `claude.md` for detailed technical information or `CHANGELOG.md` for known issues and solutions.

---

**⚠️ Use responsibly and in accordance with FanSale's terms of service**