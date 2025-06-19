# StealthMaster Resale Edition

## 🎯 Optimized for FanSale & VivaTicket Resale Tickets

This is a streamlined launcher for StealthMaster specifically configured for purchasing resale tickets on FanSale.it and VivaTicket.com. No queues, no tax codes, just fast ticket detection and purchase.

## ✨ Key Features

- **Advanced Stealth**: Uses undetected-chromedriver for better anti-detection
- **Italian Proxy Support**: Uses your existing IPRoyal proxy
- **Lightning Fast Purchase**: Automatic detection and purchase
- **No Queue Handling**: Designed for resale tickets only
- **Auto-Login**: Handles authentication automatically

## 🚀 Quick Start

1. **Setup** (one time only):
   ```bash
   ./setup_resale.sh
   ```

2. **Run the monitor**:
   ```bash
   python run_resale.py
   ```
   
   Or use the shell script:
   ```bash
   ./run_stealth.sh
   ```

3. **Monitor dashboard** (optional, in separate terminal):
   ```bash
   python monitor_dashboard.py
   ```
   Note: This is a simple status dashboard that shows monitoring statistics

## 📋 How It Works

1. **Monitoring**: Checks both FanSale and VivaTicket at optimized intervals
2. **Detection**: Looks for fixed-price (immediate purchase) tickets only
3. **Purchase**: Automatically clicks through to payment page
4. **Success**: Reserves ticket for 10 minutes for manual payment

## ⚙️ Configuration

Your existing `.env` file is used:
- FanSale credentials
- VivaTicket credentials  
- IPRoyal proxy settings
- 2Captcha API key (if needed)

The `run_resale.py` script automatically:
- Disables Ticketmaster monitoring
- Optimizes check intervals for resale sites
- Enables burst mode for faster response

## 🛡️ Anti-Detection Features

- Undetected ChromeDriver
- Browser fingerprint randomization
- Human-like behavior simulation
- Automatic proxy rotation
- CDP protocol bypass

## 📊 Performance

- Check interval: 10 seconds (normal)
- Burst mode: 3 seconds (when tickets found)
- Purchase execution: < 5 seconds
- Session management: Automatic

## 🔧 Troubleshooting

1. **Proxy not working**: Check your IPRoyal credentials in `.env`
2. **Login fails**: Manually login once when browser opens
3. **Immediate blocking**: The main StealthMaster has better stealth than lite versions

## 🎯 Target Configuration

Edit `config.yaml` to update:
- Event URLs
- Maximum price limits
- Ticket quantity preferences
- Desired sections (if any)