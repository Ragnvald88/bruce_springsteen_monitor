# StealthMaster - Advanced Ticket Reservation Bot

StealthMaster is a sophisticated, high-performance bot designed to monitor and automatically reserve tickets on Fansale.it. Built with advanced stealth capabilities, robust error handling, and intelligent automation features.

## 🚀 Features

- **Advanced Stealth Mode**: Undetected Chrome driver with anti-bot detection measures
- **Session Persistence**: Maintains login state across restarts
- **Proxy Support**: Built-in proxy authentication with IPRoyal integration
- **CAPTCHA Solving**: Automatic CAPTCHA detection and solving via 2Captcha
- **Real-time Notifications**: Telegram and Pushover support for instant alerts
- **Adaptive Delays**: Smart rate limiting to avoid detection
- **Resource Optimization**: Blocks unnecessary resources for faster performance
- **Multi-State Management**: Intelligent state machine for reliable operation

## 📋 Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- Valid Fansale.it account
- (Optional) IPRoyal proxy credentials
- (Optional) 2Captcha API key
- (Optional) Telegram bot token or Pushover credentials

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/stealthmaster.git
   cd stealthmaster
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the project root with your credentials:
   ```env
   # Fansale Credentials (REQUIRED)
   FANSALE_EMAIL="your_email@example.com"
   FANSALE_PASSWORD="your_password"

   # Proxy Configuration (OPTIONAL)
   IPROYAL_USERNAME="your_proxy_username"
   IPROYAL_PASSWORD="your_proxy_password"
   IPROYAL_HOSTNAME="geo.iproyal.com"
   IPROYAL_PORT="12321"

   # 2Captcha API Key (OPTIONAL)
   TWOCAPTCHA_API_KEY="your_2captcha_api_key"

   # Telegram Notifications (OPTIONAL)
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   TELEGRAM_CHAT_ID="your_telegram_chat_id"

   # Pushover Notifications (OPTIONAL)
   PUSHOVER_USER_KEY="your_pushover_user_key"
   PUSHOVER_API_TOKEN="your_pushover_api_token"
   ```

4. **Configure the bot**:
   Edit `config.yaml` to set your target event and preferences:
   ```yaml
   target:
     url: "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
     
   browser:
     headless: false  # Set to true for background operation
     window_size: [1280, 720]
     
   monitoring:
     check_interval: 5  # Seconds between checks
     max_tickets: 4     # Maximum tickets to reserve
   ```

## 🎯 Usage

### Basic Usage

Run the bot with default configuration:
```bash
python stealthmaster.py
```

### Test Notifications

Test your notification setup:
```bash
python notifications.py
```

### Check 2Captcha Balance

Verify your CAPTCHA solver configuration:
```bash
python captcha_solver.py
```

## 🔍 How It Works

1. **Initialization**: Bot loads configuration and creates a stealth Chrome instance
2. **Session Management**: Checks for existing session or performs fresh login
3. **Monitoring**: Continuously monitors the target page for available tickets
4. **Detection**: Uses multiple strategies to find available tickets
5. **Reservation**: Automatically clicks and adds tickets to cart
6. **Notification**: Sends alerts when tickets are successfully reserved
7. **Error Handling**: Manages blocks, CAPTCHAs, and connection issues

## ⚙️ Configuration Options

### config.yaml

| Option | Description | Default |
|--------|-------------|---------|
| `target.url` | The Fansale URL to monitor | Required |
| `browser.headless` | Run in headless mode | `false` |
| `browser.window_size` | Browser window dimensions | `[1280, 720]` |
| `monitoring.check_interval` | Seconds between page checks | `5` |
| `monitoring.max_tickets` | Maximum tickets to reserve | `4` |

### Environment Variables

All credentials should be stored in the `.env` file. See the installation section for the complete list.

## 🛡️ Security Features

- **Stealth Mode**: Hides automation indicators from detection scripts
- **Proxy Support**: Route traffic through residential proxies
- **Session Encryption**: Secure storage of login sessions
- **Resource Blocking**: Prevents tracking and reduces fingerprinting

## 🔧 Troubleshooting

### Bot Gets Blocked
- Enable proxy support in `.env`
- Increase `check_interval` in `config.yaml`
- Ensure 2Captcha is configured for CAPTCHA solving

### Login Failures
- Verify credentials in `.env`
- Check if Fansale has changed their login process
- Delete session files in `session/` directory

### No Tickets Found
- Verify the target URL is correct
- Check if the event has tickets available
- Review logs in `logs/` directory for details

### Notifications Not Working
- Test with `python notifications.py`
- Verify bot tokens and API keys
- Check network connectivity

## 📁 Project Structure

```
stealthmaster/
├── stealthmaster.py      # Main bot script
├── notifications.py      # Notification system
├── captcha_solver.py     # CAPTCHA solving integration
├── config.yaml          # Bot configuration
├── .env                 # Credentials (create this)
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── logs/               # Log files directory
└── session/            # Session storage directory
```

## 📊 Monitoring & Logs

- **Console Output**: Real-time status updates
- **Log Files**: Detailed logs in `logs/` directory with timestamps
- **Notifications**: Instant alerts for successful reservations

## ⚠️ Disclaimer

This bot is for educational purposes only. Using automated tools may violate the terms of service of ticketing websites. Users are responsible for compliance with all applicable terms and laws.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) for stealth capabilities
- [2Captcha](https://2captcha.com) for CAPTCHA solving services
- The Python community for excellent libraries and tools