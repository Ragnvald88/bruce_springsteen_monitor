# FanSale Ultimate Bot 🎯

High-performance ticket reservation bot for FanSale.it. Built for speed with a user-friendly interface, real-time statistics, and persistent settings.

## ⚡ Quick Start

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_ultimate.txt

# 2. Configure
cp .env.example .env
# Edit .env with your FanSale event URL

# 3. Run
./run_bot.py              # Launcher with Python 3.13 fix
python3 fansale_ultimate.py     # Direct execution
```

## 🚀 Features

### Core Functionality
- **Multi-browser support** (1-8 concurrent instances)
- **Smart ticket filtering** (Prato A/B, Settore, etc.)
- **CAPTCHA handling** (automatic with 2captcha or manual)
- **Anti-detection** measures with undetected ChromeDriver
- **Performance optimized** (<1s response time)

### User Interface
- **Interactive menu system** for easy navigation
- **Persistent settings** that save between runs
- **Real-time statistics** during hunting
- **Color-coded logging** for ticket notifications
- **Sound alerts** for important events

## 📊 Performance

Validated benchmarks:
- Ticket processing: **1,180,000+/second**
- Duplicate detection: **10,000,000+ lookups/second**
- Decision latency: **<10ms**

Run benchmarks:
```bash
python3 test_performance.py
```

## 📁 Project Structure

```
stealthmaster/
├── fansale_ultimate.py      # Main bot with UI and features
├── run_bot.py              # Launcher with Python 3.13 fix
├── test_performance.py      # Performance validation
├── test_ultimate_bot.py     # Unit tests
├── requirements_ultimate.txt # Dependencies
├── CLAUDE.md               # Detailed documentation
├── .env.example            # Configuration template
├── bot_settings.json       # Persistent settings
└── README.md              # This file
```

## 🔧 Configuration

Create `.env` file:
```env
FANSALE_TARGET_URL=https://www.fansale.it/tickets/all/your-event
TWOCAPTCHA_API_KEY=your_api_key  # Optional
```

## 📖 Documentation

See [CLAUDE.md](CLAUDE.md) for detailed technical documentation.

## 💡 Usage Tips

### Menu Navigation
1. **Run Bot** - Start hunting with current settings
2. **Settings** - Configure browsers, ticket types, speed, etc.
3. **Statistics** - View historical performance data
4. **Help** - Get usage tips and shortcuts

### Best Practices
- Use 2-4 browsers for optimal performance
- Set specific ticket types to reduce noise
- Enable sound alerts for purchase notifications
- Keep screenshots enabled for proof of purchase

## ⚠️ Legal Notice

This bot is for educational and defensive purposes only. Users are responsible for complying with FanSale.it's terms of service and local laws.

---

**Version**: Ultimate  
**License**: MIT