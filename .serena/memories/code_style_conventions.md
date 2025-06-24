# Code Style and Conventions

## Python Style
- **Python 3.x** (3.8+ recommended)
- **PEP 8** compliant with some flexibility
- **Type hints**: Optional but used in newer code
- **Docstrings**: Brief descriptions for classes and main methods

## Naming Conventions
- **Classes**: PascalCase (e.g., `FanSaleBot`, `StealthEnhancements`)
- **Methods/Functions**: snake_case (e.g., `hunt_and_buy`, `verify_login`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `ENHANCED_MODE`)
- **Private methods**: Leading underscore (e.g., `_internal_method`)

## Code Organization
- Main bot logic in class `FanSaleBot`
- Configuration in `__init__` method
- Core hunting loop in `hunt_and_buy` or `hunt_tickets`
- Helper methods for specific tasks (login, filtering, etc.)
- Statistics tracking throughout

## Logging Style
- Emojis for visual clarity: 🚀 (start), ✅ (success), ❌ (error), 🎫 (tickets)
- Structured format: `timestamp | level | message`
- Info level for important events, debug for details

## Error Handling
- Try-except blocks around browser operations
- Graceful degradation on failures
- Retry logic for recoverable errors
- Clean shutdown with Ctrl+C

## Threading
- Daemon threads for browser hunters
- Threading locks for purchase synchronization
- Event objects for shutdown coordination

## Browser Automation
- undetected_chromedriver for stealth
- Explicit waits over implicit waits
- JavaScript execution for clicking elements
- Screenshot capture on important events