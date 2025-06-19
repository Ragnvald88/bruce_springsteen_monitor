# StealthMaster Advanced - No BS Edition

A highly advanced, undetectable ticket monitoring system for Fansale.it (and expandable to other platforms).

## What This Actually Does

- Monitors ticket availability in real-time
- Avoids detection using REAL stealth techniques (not quantum BS)
- Alerts you instantly when tickets become available
- Works reliably without getting blocked

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements_simple.txt
   ```

2. **Configure** (edit `config_simple.yaml`):
   ```yaml
   targets:
     - platform: "fansale"
       event_name: "Your Event Name"
       url: "https://www.fansale.it/..."
       enabled: true
       interval_s: 30
   ```

3. **Run:**
   ```bash
   python stealthmaster_advanced.py
   ```

## How It Actually Works

Unlike the previous overcomplicated mess, this version:

1. **Uses undetected-chromedriver properly** - No conflicting stealth libraries
2. **Smart page checking** - Uses JavaScript instead of Selenium selectors (less detectable)
3. **Realistic behavior** - Random viewports, user agents, and subtle human simulation
4. **Intelligent intervals** - Adjusts check frequency based on time of day and ticket availability
5. **Proper error handling** - Recovers from blocks and errors gracefully

## Key Features

- **No proxy required** - Works directly (proxies were causing blocks)
- **Session persistence** - Handles cookies properly
- **Live dashboard** - See real-time stats without cluttering logs
- **Smart detection** - Checks page state before actions to avoid triggers
- **Exponential backoff** - Handles blocks intelligently

## Architecture (Simple)

```
stealthmaster_advanced.py   # Main monitor (475 lines of working code)
├── AdvancedStealth        # Real stealth configuration
├── SmartMonitor           # Intelligent monitoring logic
└── config_simple.yaml     # Simple configuration
```

## What Was Removed

- Quantum coordination (WTF was that??)
- ML optimization (no ML code existed)
- 459 lines of CDP bypass that crashes
- "Ultimate" mode that gets you blocked faster
- TLS fingerprinting (UC already does this)
- Overcomplicated error handlers
- Multiple logging systems
- Unused GUI code
- And tons more bloat...

## Future Improvements

1. **Proxy support** - When you find proxies that actually work
2. **Multi-site support** - Expand to Ticketmaster, Vivaticket
3. **Auto-purchase** - Add purchasing capability
4. **Better notifications** - Email, Discord, SMS

## Tips for Staying Undetected

1. **Don't use proxies** unless they're residential and high quality
2. **Keep intervals reasonable** - 30 seconds is fine
3. **Run one instance per event** - Don't overload
4. **Use different browsers** for different sites
5. **Clear cookies occasionally** if you get blocked

## License

Do whatever you want with it. Just don't sell it as "Quantum Ticket Master Pro" 😂
