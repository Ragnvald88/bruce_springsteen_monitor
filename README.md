# StealthMaster - FanSale Ticket Bot 🎫

A ticket purchasing bot for FanSale.it with anti-detection measures.

## Quick Start

1. **Setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/...
FANSALE_EMAIL=optional@email.com      # Only if using login
FANSALE_PASSWORD=optional_password     # Only if using login
```

2. **Run**:
```bash
python fansale_stealth.py  # Recommended - streamlined version
```

## Key Features

- 🤖 Anti-detection with undetected-chromedriver
- 🎯 Smart ticket filtering (Prato, Tribuna, etc.)
- 🔄 Automatic session refresh to avoid blocks
- 📊 Performance tracking and statistics
- 🖼️ Screenshot capture on successful checkout

## File Structure

```
fansale_stealth.py    # ← Main bot (recommended)
fansale.py           # Full-featured version
test_login.py        # Test login detection
claude.md            # Guide for Claude AI
CHANGELOG.md         # Version history & lessons
```

## Important Notes

- **404 Blocks**: Clear browser data if you get 404 errors after extended use
- **Login Optional**: Tickets can be viewed without authentication
- **Max Browsers**: Use 1-2 browsers to avoid detection

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