# StealthMaster Resale Edition

## 🎯 Optimized for FanSale & VivaTicket Resale Tickets

This is a streamlined version of StealthMaster specifically designed for purchasing resale tickets on FanSale.it and VivaTicket.com. No queues, no tax codes, just fast ticket detection and purchase.

## ✨ Key Features

- **Single Browser Instance**: Fast and resource-efficient
- **7-Minute Session Rotation**: Avoids the 10-minute bot detection
- **Lightning Fast Purchase**: < 2 seconds from detection to checkout
- **Italian Proxy Support**: Uses your existing IPRoyal proxy
- **No Queue Handling**: Designed for resale tickets only
- **Auto-Login**: Handles authentication automatically

## 🚀 Quick Start

1. **Setup** (one time only):
   ```bash
   ./setup_resale.sh
   ```

2. **Run the monitor**:
   
   Option A - Lite version (recommended):
   ```bash
   python stealthmaster_lite.py
   ```
   
   Option B - Use existing system:
   ```bash
   python run_resale.py
   ```

3. **Monitor dashboard** (optional, in separate terminal):
   ```bash
   python monitor_dashboard.py
   ```

## 📋 How It Works

1. **Monitoring**: Checks both FanSale and VivaTicket every 1.5 seconds
2. **Detection**: Looks for fixed-price (immediate purchase) tickets only
3. **Purchase**: Automatically clicks through to payment page
4. **Success**: Reserves ticket for 10 minutes for manual payment

## ⚙️ Configuration

Your existing `.env` file is used:
- FanSale credentials
- VivaTicket credentials  
- IPRoyal proxy settings

The system automatically:
- Sets Italian locale and timezone
- Uses Italian proxy endpoints
- Handles cookie acceptance
- Manages login sessions

## 🎫 What Tickets It Finds

- **FanSale**: Only "Prezzo fisso" (fixed price) offers
- **VivaTicket**: Only available resale tickets
- **Price**: Respects max_price from config.yaml
- **Quantity**: Attempts to get requested quantity

## ⚡ Performance

- Session rotation: Every 7 minutes (before 10-minute detection)
- Check frequency: 1.5 seconds
- Purchase speed: < 2 seconds
- Resource usage: ~300-500 MB RAM

## 🛠️ Troubleshooting

**Bot protection detected:**
- The system automatically rotates sessions
- If persistent, restart the script

**Login fails:**
- Check credentials in .env file
- Ensure account is not locked

**No tickets found:**
- Resale tickets are rare - be patient
- Check that events are enabled in config.yaml

**Purchase fails:**
- Usually means ticket was already sold
- System will continue monitoring for next ticket

## 📝 Files Created

- `stealthmaster_lite.py` - Optimized monitoring script
- `run_resale.py` - Launcher for existing system
- `monitor_dashboard.py` - Real-time status dashboard
- `setup_resale.sh` - One-time setup script

## 🎯 Success Tips

1. **Be Ready**: Have payment method ready when ticket is found
2. **Stay Alert**: You have 10 minutes to complete payment
3. **Multiple Tickets**: System will try to get your desired quantity
4. **Peak Times**: More tickets available closer to event date

## ⚠️ Important Notes

- This is for personal use only
- Respect the platforms' terms of service
- The system finds tickets but YOU must complete payment
- Success depends on ticket availability

Good luck getting your Bruce Springsteen tickets! 🎸
