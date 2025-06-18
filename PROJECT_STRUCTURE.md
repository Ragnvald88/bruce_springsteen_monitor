# StealthMaster v2.0 - Clean Project Structure

## Project Overview
After cleanup, the StealthMaster project now has a clean, focused structure with only essential files.

## Directory Structure

```
stealthmaster/
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore rules
├── config.yaml          # Main configuration file
├── gui_launcher.py      # GUI launcher with error handling
├── requirements.txt     # Python dependencies
├── run.sh              # Shell script launcher
├── stealthmaster.py     # Main entry point
├── test_enhancements.py # Test script for new features
│
├── src/                 # Source code
│   ├── browser/         # Browser management
│   │   ├── launcher.py  # Browser launcher
│   │   └── pool_manager.py # Browser pool management
│   │
│   ├── core/           # Core functionality
│   │   └── (core modules)
│   │
│   ├── database/       # Database operations
│   │   └── statistics.py
│   │
│   ├── detection/      # Ticket detection
│   │   ├── __init__.py
│   │   └── ticket_detector.py # Enhanced detector
│   │
│   ├── profiles/       # Profile management
│   │   └── manager.py
│   │
│   ├── stealth/        # Anti-detection
│   │   ├── akamai_bypass.py
│   │   └── ultimate_bypass.py
│   │
│   ├── telemetry/      # Data tracking (NEW)
│   │   ├── __init__.py
│   │   └── data_tracker.py # Data usage monitoring
│   │
│   ├── ui/             # User interfaces
│   │   └── advanced_gui.py
│   │
│   └── utils/          # Utilities
│       ├── config_validator.py
│       ├── logging.py
│       ├── notifications.py # Fixed with confidence param
│       └── retry_manager.py
│
├── logs/               # Log files
├── data/               # Data storage
├── venv/               # Virtual environment
│
└── docs/               # Documentation
    ├── README.md
    ├── QUICK_START.md
    ├── AKAMAI_BYPASS.md
    ├── ENHANCED_FEATURES_GUIDE.md
    └── IMPLEMENTATION_SUMMARY.md
```

## Removed Files (66 total)

### Unused Python Modules (40 files)
- Removed obsolete src/main.py (replaced by stealthmaster.py)
- Removed unused platform-specific modules
- Removed duplicate/obsolete stealth modules
- Removed unused network and orchestration modules

### Test Files (7 files)
- Kept only test_enhancements.py
- Removed old test files

### Cache & Temp Files (17 directories)
- All __pycache__ directories
- .DS_Store files
- .pytest_cache directories

### Other (2 files)
- requirements_cleaned.txt (duplicate)
- implementationplan.md (obsolete doc)

## Key Improvements

1. **Cleaner Structure**: Only essential files remain
2. **No Duplicates**: Removed redundant modules
3. **Better Organization**: Clear separation of concerns
4. **Enhanced Features**: Added telemetry and improved detection
5. **Fixed Issues**: Corrected notification manager parameter

## Active Components

### Core Systems
- **Browser Management**: Single browser per platform approach
- **Ticket Detection**: Platform-specific with confidence scoring
- **Data Tracking**: Real-time usage monitoring
- **Stealth**: Akamai bypass and ultimate mode

### Entry Points
- `stealthmaster.py` - Main CLI interface
- `gui_launcher.py` - GUI launcher
- `run.sh` - Shell script launcher

### Configuration
- `config.yaml` - All settings in one place
- `.env` - Environment variables for sensitive data

## Next Steps

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure**: Edit `config.yaml` with your settings
3. **Run**: `python stealthmaster.py` or `./run.sh`
4. **Monitor**: Check logs/telemetry/ for usage data

The project is now clean, organized, and ready for production use!
