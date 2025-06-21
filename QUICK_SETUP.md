# StealthMaster Ultimate - Quick Setup Guide

## ✅ YES, IT WILL AUTO-RESERVE TICKETS!

Here's exactly how the auto-reserve works:

1. **Monitors** the page every 5 seconds for new tickets
2. **Detects** new listings by comparing with previously seen tickets
3. **Filters** tickets by your max price (€500 default)
4. **Clicks** on the ticket automatically
5. **Finds** and clicks the "Add to Cart" button
6. **Verifies** the ticket was added to cart
7. **Logs** everything to files

## 🚀 Quick Start (2 minutes)

### Step 1: Edit config.yaml
```yaml
email: "your-email@example.com"      # ← Add your Fansale email
password: "your-password"            # ← Add your Fansale password
```

### Step 2: Run the bot
```bash
python stealthmaster_ultimate.py
```

That's it! The bot will:
- Log into Fansale automatically
- Start monitoring for tickets
- Reserve them automatically when found

## ⚙️ Key Settings in config.yaml

- `auto_reserve: true` - Enables automatic reservation (THIS IS ON BY DEFAULT!)
- `max_price: 500` - Won't reserve tickets over €500
- `quantity: 1` - Reserves 1 ticket then stops
- `check_interval: 5` - Checks every 5 seconds
- `proxy: null` - Add proxy here if needed

## 📁 Clean Project Structure

We now have only these files:
- `stealthmaster_ultimate.py` - The ONE script you need
- `config.yaml` - Your configuration
- `config_example.yaml` - Example configuration
- `STEALTHMASTER_GUIDE.md` - Detailed documentation
- `QUICK_SETUP.md` - This file

All old versions have been removed!

## 🌐 Proxy Verification

If using a proxy:
1. Set it in config.yaml: `proxy: "http://user:pass@proxy:port"`
2. The bot will verify it's working on startup
3. Check `logs/proxy_usage_*.log` for verification

## 📊 Tracking Reservations

The bot creates these logs:
- `logs/reservations_*.json` - Each ticket reserved
- `logs/lifetime_reservations.json` - Running total
- `logs/session_report_*.json` - Full session details
- `logs/all_sessions.jsonl` - Quick summary of all sessions

## ⚠️ Important Notes

1. **YOU MUST BE LOGGED IN** - Fansale shows no tickets to guests!
2. The bot will automatically log in using your credentials
3. It saves session cookies for faster reconnection
4. Dashboard shows real-time stats including bandwidth usage

## 🎯 How It Knows to Reserve

When the bot finds new tickets, this code runs:
```python
if self.auto_reserve:  # This is TRUE by default
    # Sorts tickets by price (cheapest first)
    # Tries to reserve up to 'quantity' tickets
    # Calls smart_reserve_ticket() which:
    #   1. Clicks the ticket
    #   2. Clicks "Add to Cart"
    #   3. Verifies success
```

Ready to go! Just add your credentials and run it.