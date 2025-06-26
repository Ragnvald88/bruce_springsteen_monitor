# Code Style and Conventions

## Python Style Guidelines
- **Python Version**: 3.x (compatible with 3.8+)
- **Style Guide**: Generally follows PEP 8 with some variations
- **Line Length**: No strict limit, but generally kept reasonable

## Naming Conventions
- **Classes**: PascalCase (e.g., `FanSaleBot`, `StatsManager`, `NotificationManager`)
- **Functions/Methods**: snake_case (e.g., `hunt_tickets`, `purchase_ticket`, `create_browser`)
- **Constants**: UPPER_CASE (e.g., `Colors.HEADER`, `Colors.GREEN`)
- **Private Methods**: Leading underscore (e.g., `_get_memory_usage`)

## Type Hints
- Uses type hints extensively for function parameters and returns
- Common imports: `from typing import Dict, List, Optional, Tuple, Set`
- Dataclasses used for configuration: `@dataclass`

## Documentation
- **Module Docstrings**: Triple quotes at file beginning describing purpose
- **Class Docstrings**: Brief description in triple quotes
- **Method Docstrings**: Brief description of functionality
- **Inline Comments**: Used sparingly for complex logic

## Code Organization
- **Imports**: Grouped by standard library, third-party, local
- **Class Structure**: 
  1. Class docstring
  2. `__init__` method
  3. Public methods
  4. Private methods
- **Threading**: Uses threading.Lock for synchronization
- **Decorators**: Custom retry decorator for resilient operations

## Error Handling
- Try-except blocks for all external operations
- Specific exception handling where possible
- Logging errors with context
- Graceful degradation on failures

## Logging
- Custom ColoredFormatter for terminal output
- Log levels: INFO for important events, WARNING for issues, ERROR for failures
- Emoji indicators for visual clarity (🎫, 🚀, ✅, ❌, etc.)

## Performance Considerations
- JavaScript execution preferred over Selenium clicks
- Minimal waits between actions
- Thread-safe operations for shared state
- Early filtering with hash-based duplicate detection