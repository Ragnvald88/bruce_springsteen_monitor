# FanSale Bot 🎫

A powerful ticket bot for FanSale.it with multi-browser support, intelligent filtering, and automatic purchasing.

## Features

- **Multi-Browser Support**: Run 1-5 browsers simultaneously
- **Smart Ticket Filtering**: Target specific sections (e.g., Prato A, Tribuna)
- **Auto-Purchase**: Reserves up to 4 tickets automatically
- **Proxy Support**: Data-saving mode when using proxy
- **Persistent Login**: Browser profiles save login state
- **Login Verification**: Checks login status every 5 minutes
- **Statistics Tracking**: Detailed logging of all activities
- **Checkout Alarm**: Audio alert when tickets secured
- **Screenshot Capture**: Saves screenshots on successful checkout

## Quick Start

1. **Setup Environment**:
```bash
# Create .env file
FANSALE_EMAIL=your@email.com
FANSALE_PASSWORD=yourpassword
FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554

# Optional proxy
IPROYAL_USERNAME=your_username
IPROYAL_PASSWORD=your_password
IPROYAL_HOSTNAME=geo.iproyal.com
IPROYAL_PORT=12321
```

2. **Install Dependencies**:
```bash
pip install undetected-chromedriver selenium-wire python-dotenv
```

3. **Run Bot**:
```bash
python fansale.py
```

## Usage

The bot provides a menu with these options:

1. **Start Bot** - Configure and run the ticket hunter
2. **Clear Browser Profiles** - Remove saved login data
3. **Show Statistics** - View performance metrics
4. **Test Filters** - Debug mode to test ticket filtering
5. **Exit** - Close the program

## Ticket Filtering

The bot can filter tickets by keywords found in the ticket description:

### Common Italian Concert Sections:
- **Prato** - Lawn/standing area (e.g., "Prato A", "Prato B")
- **Parterre** - Floor/pit area
- **Tribuna** - Tribune/stands
- **Settore** - Sector (e.g., "Settore 1", "Settore 2")
- **Anello** - Ring level
- **Numerato** - Numbered seats

### Filter Examples:
- `Prato A` - Only tickets containing "Prato A"
- `Tribuna` - Any tribune tickets
- `Settore 1, Settore 2` - Tickets from sector 1 OR sector 2
- `Prato, Gold` - Tickets containing "Prato" OR "Gold"

### Filter Modes:
- **ANY**: Accepts tickets matching ANY of the keywords (default)
- **ALL**: Only accepts tickets matching ALL keywords

## Configuration Options

- **Browsers**: 1-5 (recommended 2-3)
- **Proxy**: Enable for data saving (blocks images/CSS)
- **Max Tickets**: Automatically reserves up to 4
- **Filters**: Optional keywords to target specific sections

## Performance

| Browsers | Checks/Minute |
|----------|--------------|
| 1 | ~20 |
| 2 | ~30 |
| 3 | ~35 |
| 4+ | ~40 |

## Tips

- Use filters to target the best sections
- Test filters first using option 4 before starting the hunt
- Start with 2-3 browsers for optimal balance
- Use proxy to save data costs
- Browser profiles persist logins between runs
- Check `fansale_bot.log` for detailed activity
- Screenshots saved as `checkout_[timestamp].png`

## Statistics Tracked

- Total checks performed
- Times no tickets found
- Times tickets detected (matching filters)
- Successful checkouts
- Already reserved tickets

## Example Workflow

1. Run `python fansale.py`
2. Choose option 4 to test filters
3. Enter "Prato A" to only get Prato A tickets
4. Verify filters work correctly
5. Choose option 1 to start bot
6. Configure 2-3 browsers
7. Let it hunt for matching tickets!

---

**Note**: Use responsibly and in accordance with FanSale's terms of service.
