# 🥷 Bruce Springsteen Ticket Monitor - Ultra-Stealth Edition

Advanced ticket monitoring system with sophisticated anti-detection capabilities for Bruce Springsteen concerts across multiple platforms.

## 🌟 Features

- **Multi-Platform Support**: Ticketmaster, FanSale, VivaTicket
- **Advanced Stealth**: Dynamic profiles, TLS fingerprinting, behavioral simulation
- **Smart Monitoring**: Adaptive intervals, burst mode, priority-based scheduling
- **Robust Architecture**: Connection pooling, caching, graceful error handling
- **Multiple Operation Modes**: Stealth, Beast, Adaptive, Ultra-Stealth, Hybrid
- **GUI Interface**: User-friendly graphical interface with real-time monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd bruce_springsteen_monitor

# Install dependencies
pip install -r requirements.txt

# Install playwright browsers
playwright install

# Setup environment variables (optional)
cp .env.example .env
# Edit .env with your proxy credentials if needed
```

### Basic Usage

```bash
# Run with default configuration
python src/main.py

# Run with GUI interface
python src/main.py --gui

# Run in ultra-stealth mode
python src/main.py --mode ultra_stealth

# Run with custom config
python src/main.py --config config/my_config.yaml
```

### Using Make Commands

```bash
# See all available commands
make help

# Setup development environment
make setup-dev

# Run tests
make test

# Run the monitor
make run

# Run with GUI
make run-gui
```

## 📋 Configuration

The system uses YAML configuration files located in the `config/` directory.

### Main Configuration (`config/config.yaml`)

```yaml
app_settings:
  mode: "adaptive"  # stealth, beast, hybrid, adaptive, ultra_stealth
  dry_run: false

targets:
  - platform: "ticketmaster"
    event_name: "Bruce Springsteen San Siro 2025"
    url: "https://shop.ticketmaster.it/..."
    enabled: true
    priority: "HIGH"
    interval_s: 45
    max_price_per_ticket: 300.00

monitoring_settings:
  default_interval_s: 60
  min_monitor_interval_s: 15

profile_manager:
  num_target_profiles: 20
  profiles_per_platform: 5
  enable_tls_rotation: true
  enable_behavioral_warmup: true
```

### Operation Modes

- **`adaptive`**: Dynamically adjusts strategy based on detection
- **`stealth`**: Prioritizes avoiding detection over speed
- **`ultra_stealth`**: Maximum anti-detection, minimal footprint
- **`beast`**: Maximum speed, accepts higher detection risk
- **`hybrid`**: Balanced approach between stealth and performance

## 🏗️ Architecture

### Core Components

- **`UnifiedOrchestrator`**: Main coordination engine
- **`ProfileManager`**: Dynamic browser profile management
- **`ConnectionPoolManager`**: HTTP client pooling with stealth features
- **`StealthEngine`**: Anti-detection strategies
- **`StrikeForce`**: High-speed ticket acquisition engine

### Profile System

The system uses sophisticated browser profiles with:
- Dynamic user agents and viewport sizes
- TLS fingerprint randomization
- Behavioral simulation (typing speed, mouse movements)
- Session persistence and rotation
- Health monitoring and auto-replacement

### Anti-Detection Features

- **TLS Fingerprinting**: Mimics real browser TLS signatures
- **Behavioral Simulation**: Human-like interaction patterns
- **Connection Rotation**: Automatic client rotation to avoid patterns
- **Header Randomization**: Dynamic HTTP header generation
- **Proxy Support**: Rotating proxy infrastructure

## 🧪 Testing

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run with coverage
make test-coverage

# Quick diagnostic test
make test-quick

# Advanced stealth test
make test-stealth
```

### Test Structure

- `tests/test_profiles_manager.py` - Profile management tests
- `tests/test_connection_manager.py` - HTTP client tests
- `tests/test_config_loading.py` - Configuration tests
- `tests/test_models.py` - Data model tests

## 🔧 Development

### Code Quality Tools

```bash
# Format code
make format

# Run linting
make lint

# Clean temporary files
make clean
```

### Adding New Platforms

1. Create a new monitor class in `src/platforms/`
2. Implement the required interface methods
3. Add platform configuration to `config.yaml`
4. Update the orchestrator to include the new platform

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 🔐 Security & Privacy

- **No Data Collection**: The system doesn't store personal information
- **Local Operation**: All processing happens locally
- **Secure Configuration**: Sensitive data stored in environment variables
- **Anti-Fingerprinting**: Advanced techniques to avoid detection

## 📊 Monitoring & Logging

The system provides comprehensive logging:

- **Console Output**: Real-time status updates
- **File Logging**: Detailed logs in `logs/` directory
- **Error Tracking**: Separate error log for debugging
- **Performance Metrics**: Connection pool and profile statistics

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARNING`: Important notices
- `ERROR`: Error conditions
- `CRITICAL`: Critical failures

## 🚨 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

**Playwright Issues**
```bash
# Reinstall playwright browsers
playwright install --force
```

**Profile Loading Errors**
```bash
# Clear profile cache
rm -rf storage/profiles/
rm profiles_backup.json
```

**Network Connectivity**
```bash
# Test network diagnostics
python Testing_Scripts/quick_network_diagnostic.py
```

## 📈 Performance Tuning

### For Maximum Speed (Beast Mode)
- Increase `max_parallel` in strike settings
- Reduce `interval_s` for targets
- Lower `selection_quality_min_tier` in profile manager

### For Maximum Stealth (Ultra-Stealth Mode)
- Set `max_parallel: 1` in strike settings
- Increase `base_target_interval_multiplier`
- Set `selection_quality_min_tier: 5`

### Memory Optimization
- Adjust `data_limits` in configuration
- Enable `optimization_thresholds`
- Monitor `cache.max_size_mb`

## 📄 License

This project is for educational purposes only. Please respect the terms of service of the platforms you're monitoring.

## ⚠️ Disclaimer

This software is provided as-is for educational and research purposes. Users are responsible for complying with all applicable laws and terms of service. The authors assume no responsibility for any misuse of this software.

---

Made with ❤️ for Bruce Springsteen fans worldwide 🎸