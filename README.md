# 🎯 StealthMaster - Automated Ticket Monitoring System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

StealthMaster is an advanced ticket monitoring system with stealth capabilities designed to help you find and reserve tickets from major platforms.

## 🚀 Features

- **Multi-Platform Support**: Monitors Ticketmaster, Fansale, and Vivaticket simultaneously
- **Stealth Technology**: Advanced anti-detection with CDP bypass and fingerprint randomization
- **Live Dashboard**: Real-time monitoring status with visual indicators
- **Smart Monitoring**: Configurable check intervals with burst mode when tickets are found
- **Session Persistence**: Saves cookies and maintains login sessions
- **Proxy Support**: Built-in support for residential proxies (IPRoyal configured)

## 📋 Prerequisites

- Python 3.11+ (works with 3.13)
- Google Chrome installed
- Active accounts on ticket platforms
- (Optional) 2Captcha API key for CAPTCHA solving
- (Optional) IPRoyal proxy credentials

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/stealthmaster.git
cd stealthmaster
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure credentials**
```bash
cp .env.example .env
# Edit .env with your credentials
```

## ⚙️ Configuration

Edit `config.yaml` to set your monitoring targets:

```yaml
targets:
  - platform: "fansale"
    event_name: "Bruce Springsteen Milano 2025"
    url: "https://www.fansale.it/..."
    enabled: true
    priority: "urgent"  # low, normal, high, urgent
    interval_s: 30
    max_price_per_ticket: 800
    min_ticket_quantity: 1
    max_ticket_quantity: 8
```

## 🎮 Usage

### Start StealthMaster with Live Dashboard

```bash
./run.sh
# OR
python stealthmaster.py
```

### Dashboard Interface

```
🎯 StealthMaster - Ticket Monitor
┌─────────────────────────────────────────────────────────────┐
│ 📊 Session Statistics          │ 🖥️  Active Monitors        │
│ Uptime: 0:15:42               │ Platform  Event    Status  │
│ Active Monitors: 2            │ Fansale   Bruce... 🟢 Active│
│ Tickets Found: 12             │ Ticketm.. Bruce... 🔄 Check │
│ Tickets Reserved: 3           │                            │
│ Success Rate: 25.0%           │                            │
└─────────────────────────────────────────────────────────────┘
```

### Status Indicators

- ⏳ **Starting** - Monitor initializing
- 🔄 **Checking** - Currently checking for tickets
- 🟢 **Active** - Monitor running normally
- 🎉 **Reserved!** - Successfully reserved tickets
- ❌ **Sold out** - Tickets unavailable
- ⚠️  **Error** - Connection or other issue

## 🔧 Advanced Features

### Priority Levels

Configure monitoring intensity with priority levels:

- **low**: Check every 60-120s
- **normal**: Check every 30-60s (default)
- **high**: Check every 10-30s
- **urgent**: Check every 5-10s with maximum resources

### Burst Mode

When tickets are found, automatically switches to rapid checking (5-second intervals) to maximize reservation chances.

### Stealth Features

- Undetected ChromeDriver integration
- Browser fingerprint randomization
- Human-like behavior simulation
- TLS fingerprint rotation
- CDP protocol bypass

## 📁 Project Structure

```
stealthmaster/
├── stealthmaster.py      # Main entry point with UI
├── config.yaml          # Configuration file
├── .env                 # Your credentials (create from .env.example)
├── src/                 # Source code
│   ├── browser/         # Browser automation
│   ├── platforms/       # Platform-specific handlers
│   ├── stealth/         # Anti-detection measures
│   └── ui/              # User interface components
└── logs/                # Application logs
```

## 🐛 Troubleshooting

### Chrome not found
Ensure Chrome is installed in `/Applications/Google Chrome.app` on macOS

### Login required
The browser will open visibly on first run - manually login when prompted

### Proxy errors
Set `proxy_settings.enabled: false` in config.yaml if you don't have proxies

## 📊 Monitoring Tips

1. **Start with normal priority** and increase if needed
2. **Set realistic price limits** to avoid overpaying
3. **Use burst mode** for high-demand events
4. **Monitor logs** in the `logs/` directory for detailed information

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational purposes. Always comply with website terms of service and local regulations regarding automated ticket purchasing.