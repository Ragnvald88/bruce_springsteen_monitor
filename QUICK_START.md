# 🚀 StealthMaster Quick Start Guide

## ✅ Prerequisites Completed
- ✓ Chrome installed at `/Applications/Google Chrome.app`
- ✓ Python virtual environment set up
- ✓ All dependencies installed
- ✓ `.env` file created with your credentials

## 🎯 Starting StealthMaster

### Option 1: Using the run script (Recommended)
```bash
./run.sh
```

### Option 2: Direct Python execution
```bash
source venv/bin/activate
python -m src.main
```

## 📋 Current Configuration

### Active Targets
1. **Fansale - Bruce Springsteen Milano 2025**
   - Status: ✅ ENABLED
   - Check interval: 30 seconds
   - Burst mode: 5 seconds when tickets found
   - Max price: €800 per ticket
   - Quantity: 2-4 tickets

2. **Ticketmaster - Bruce Springsteen San Siro 2025**
   - Status: ❌ DISABLED (enable in config.yaml when ready)
   - Check interval: 30 seconds
   - Max price: €750 per ticket

### Your Credentials (from .env)
- ✅ Fansale: ronaldhoogenberg@hotmail.com
- ✅ Ticketmaster: ronaldhoogenberg@gmail.com  
- ✅ Vivaticket: ronaldhoogenberg@gmail.com
- ✅ IPRoyal Proxy: Configured (Italy)
- ✅ 2Captcha: API key configured

## 🎮 What Happens When You Start

1. **Browser Launch**: StealthMaster opens a Chrome browser with stealth patches
2. **Dashboard**: A terminal dashboard shows real-time statistics
3. **Monitoring**: The bot checks Fansale every 30 seconds for tickets
4. **Notifications**: When tickets are found, burst mode activates (5-second checks)
5. **Stealth**: Advanced anti-detection measures are active:
   - CDP bypass
   - Human-like behavior
   - Fingerprint randomization
   - TLS fingerprint rotation

## ⚙️ Customization

### Enable More Platforms
Edit `config.yaml` and set `enabled: true` for Ticketmaster or Vivaticket

### Adjust Check Intervals
In `config.yaml`, modify `interval_s` for each target

### Change Ticket Preferences
Update in `config.yaml`:
- `desired_sections`: Preferred seating areas
- `max_price_per_ticket`: Maximum price willing to pay
- `min/max_ticket_quantity`: Number of tickets to buy

## 🚨 Important Notes

1. **First Run**: The browser will open in non-headless mode so you can see it working
2. **Login**: You may need to manually login to Fansale on first run
3. **Sessions**: Cookies are saved for future runs
4. **Detection**: If blocked, the system will rotate profiles and retry

## 🛑 Stopping

Press `Ctrl+C` in the terminal to stop monitoring

## 📊 Monitoring Dashboard

The dashboard shows:
- Active monitors and their status
- Success/failure rates
- Detection events
- Resource usage
- Ticket opportunities found

## 🆘 Troubleshooting

1. **Chrome not found**: Make sure Chrome is installed in Applications
2. **Login issues**: Manually login in the browser window
3. **Proxy errors**: Disable proxy in config.yaml if needed
4. **No tickets found**: This is normal - tickets are scarce!

Ready to start? Run `./run.sh` and happy hunting! 🎫