# StealthMaster Architecture

## Overview

StealthMaster is an advanced ticket monitoring and purchasing bot built with Python, using Playwright/Selenium for browser automation and incorporating sophisticated anti-detection measures.

## Project Structure

```
stealthmaster/
├── stealthmaster.py          # Main entry point (production version)
├── gui_launcher.py           # GUI launcher wrapper
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
│
├── src/                     # Core application modules
│   ├── browser/            # Browser management and automation
│   ├── config.py           # Configuration management
│   ├── constants.py        # Application constants
│   ├── database/           # Statistics and data persistence
│   ├── detection/          # Bot detection monitoring and evasion
│   ├── network/            # Request interception and management
│   ├── orchestration/      # Workflow and task orchestration
│   ├── platforms/          # Platform-specific implementations
│   ├── profiles/           # User profile management
│   ├── stealth/            # Anti-detection techniques
│   ├── telemetry/          # Data tracking and analytics
│   ├── ui/                 # User interfaces (CLI/GUI)
│   └── utils/              # Utility functions
│
├── tests/                  # Test suite
├── data/                   # Runtime data (cookies, profiles)
├── logs/                   # Application logs
└── archive/                # Archived versions and old docs
```

## Core Components

### 1. Browser Management (`src/browser/`)
- **launcher.py**: Manages browser instances with stealth configurations
- **pool.py**: Browser pool management for concurrent operations
- **context.py**: Browser context management with profile support

### 2. Detection & Stealth (`src/detection/` & `src/stealth/`)
- **monitor.py**: Real-time detection monitoring
- **recovery.py**: Automated recovery strategies
- **adaptive_response.py**: Dynamic response to detection attempts
- **akamai_bypass.py**: Specific bypasses for Akamai protection
- **ultimate_bypass.py**: Advanced anti-detection techniques
- **behaviors.py**: Human-like behavior simulation

### 3. Network Management (`src/network/`)
- **interceptor.py**: Request/response interception and modification
- **rate_limiter.py**: Intelligent rate limiting
- **session.py**: Session management and persistence
- **tls_fingerprint.py**: TLS fingerprint randomization

### 4. Platform Support (`src/platforms/`)
- **base.py**: Abstract base handler for all platforms
- **fansale.py**: Fansale.de specific implementation
- **ticketmaster.py**: Ticketmaster implementation
- **vivaticket.py**: Vivaticket implementation

### 5. User Interface (`src/ui/`)
- **terminal_dashboard.py**: Rich CLI dashboard
- **advanced_gui.py**: Tkinter-based GUI
- **web_dashboard.py**: Web-based dashboard (Flask)

## Key Features

### Anti-Detection System
- Canvas fingerprint spoofing
- WebGL metadata randomization
- Audio context fingerprint variation
- Font fingerprint randomization
- WebRTC leak prevention
- Timezone and language spoofing
- Hardware concurrency randomization
- Screen resolution spoofing

### Browser Automation
- Undetected Chrome/Chromium driver
- Playwright integration for advanced scenarios
- Session persistence and cookie management
- Proxy support with authentication
- Browser pool for parallel operations

### Monitoring & Detection
- Real-time ticket availability monitoring
- Multi-platform support
- Intelligent retry mechanisms
- Progressive backoff strategies
- Detection pattern analysis

### Data Management
- SQLite database for statistics
- Profile persistence
- Cookie management
- Telemetry and analytics
- History tracking

## Configuration

The application is configured via `config.yaml`:

```yaml
profiles:
  - email: user@example.com
    password: password
    phone: "+1234567890"

targets:
  - platform: fansale
    artist: "Bruce Springsteen"
    venue: "Olympiastadion Berlin"
    date: "2025-07-03"
    
monitoring:
  interval: 5
  timeout: 30
  
browser:
  headless: false
  viewport:
    width: 1920
    height: 1080
```

## Usage Modes

### 1. CLI Mode (Default)
```bash
python stealthmaster.py
```

### 2. GUI Mode
```bash
python stealthmaster.py --gui
# or
python gui_launcher.py
```

### 3. Ultimate Mode (Maximum Stealth)
```bash
python stealthmaster.py --ultimate
```

## Security Considerations

- Credentials are stored locally
- Proxy authentication is handled securely
- No data is sent to external servers
- All automation respects rate limits
- Detection evasion is for legitimate ticket purchases only

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Benchmarking
```bash
python project_audit.py
```

### Adding New Platforms
1. Create a new handler in `src/platforms/`
2. Inherit from `BasePlatformHandler`
3. Implement required methods
4. Add platform constants to `src/constants.py`

## Troubleshooting

- Check `logs/` directory for detailed error logs
- Ensure `config.yaml` is properly configured
- Verify all dependencies are installed
- Run benchmarking tool to identify issues

## License

This project is for educational purposes only. Always respect website terms of service and use responsibly.