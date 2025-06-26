# Project Overview

## Purpose
FanSale Bot is an automated ticket monitoring and reservation system for FanSale.it. It operates without login requirements and uses multiple concurrent browsers to maximize ticket detection speed.

## Tech Stack
- **Language**: Python 3.x
- **Core Libraries**:
  - `undetected-chromedriver` (>=3.5.5) - For stealth browser automation
  - `selenium` (>=4.0.0) - Web automation framework
  - `python-dotenv` (>=1.0.0) - Environment variable management
- **System**: Darwin (macOS)
- **Browser**: Chrome with undetected ChromeDriver

## Key Features
1. **Multi-Browser Hunting**: Parallel browser threads for concurrent monitoring
2. **Ticket Type Categorization**: Prato A, Prato B, Settore (seated), Other
3. **Duplicate Detection**: MD5 hashing to avoid re-processing tickets
4. **Persistent Statistics**: Thread-safe statistics tracking across sessions
5. **Anti-Detection Mechanisms**: Stealth mode, session refreshing, block recovery
6. **Health Monitoring**: System and browser health tracking
7. **Notification System**: Alerts for ticket discoveries

## Configuration
- **Environment Variables**: `.env` file with `FANSALE_TARGET_URL`
- **Bot Configuration**: `bot_config.json` with runtime settings
- **Browser Profiles**: Persistent Chrome profiles in `browser_profiles/`
- **Statistics**: `fansale_stats.json` for tracking performance metrics