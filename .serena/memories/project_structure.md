# Project Structure

## Root Directory Files
- **fansale.py**: Main bot implementation (1160 lines)
- **CLAUDE.md**: Detailed documentation for AI assistance
- **.env.example**: Environment variable template
- **.gitignore**: Version control exclusions
- **bot_config.json**: Runtime configuration
- **fansale_stats.json**: Persistent statistics storage
- **fansale_bot.log**: Runtime logging output

## Directories
- **venv/**: Python virtual environment
- **browser_profiles/**: Persistent Chrome profiles for each browser instance
- **screenshots/**: Captured images on successful ticket reservations
- **archive/**: Historical files including requirements.txt
- **.serena/**: Serena coding assistant workspace
- **.claude/**: Claude AI workspace
- **.vscode/**: VS Code editor configuration
- **__pycache__/**: Python bytecode cache

## Key Classes in fansale.py
1. **BotConfig**: Configuration dataclass with defaults
2. **StatsManager**: Thread-safe statistics management
3. **NotificationManager**: Alert system for ticket discoveries
4. **HealthMonitor**: Browser and system health tracking
5. **FanSaleBot**: Main bot class with core logic
6. **Colors**: ANSI color codes for terminal output
7. **ColoredFormatter**: Custom logging formatter

## Data Flow
1. Configuration loaded from .env and bot_config.json
2. Multiple browser instances created with unique profiles
3. Each browser runs in separate thread hunting tickets
4. Tickets detected via CSS selectors and processed for duplicates
5. Matching tickets trigger immediate purchase attempts
6. Statistics updated in thread-safe manner
7. Screenshots captured on successful reservations

## Critical Performance Paths
- **hunt_tickets()**: Main monitoring loop (lines 674-802)
- **purchase_ticket()**: Speed-critical reservation logic (lines 803-847)
- **extract_full_ticket_info()**: Ticket parsing and categorization
- **generate_ticket_hash()**: Duplicate detection via MD5