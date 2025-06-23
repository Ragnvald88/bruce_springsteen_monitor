# StealthMaster Project Structure

## Active Files (Focus Here)
```
├── fansale_stealth.py     # ⭐ MAIN BOT - Use this (495 lines, stable)
├── fansale.py             # Alternative full version (1151 lines, complex)
├── test_login.py          # Utility to test login detection
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (git-ignored)
└── claude.md              # Quick reference for Claude
```

## Documentation
```
├── README.md              # User-facing documentation
├── CHANGELOG.md           # Version history & lessons learned
└── PROJECT_STRUCTURE.md   # This file
```

## Generated/Runtime
```
├── browser_profiles/      # Persistent browser sessions
├── screenshots/           # Successful ticket captures  
├── stats.json            # Performance metrics
├── fansale_bot.log       # Runtime logs
└── debug.log             # Detailed debug info
```

## Archived (Historical Reference)
```
└── archive/
    ├── fansale_new_test.py    # Terminal UI experiment
    ├── DEEP_ANALYSIS.md       # Old analysis
    ├── LOGIN_FIX.md           # Old bug documentation
    ├── PROJECT_ANALYSIS.md    # Old project notes
    └── QUICKSTART.md          # Old quick start guide
```

## Hidden/Ignored
```
├── .claude-ignore         # Files Claude should ignore
├── .gitignore            # Git ignore rules
├── venv/                 # Python virtual environment
└── utilities/            # Optional enhancement modules
```

## Decision Tree for Claude Code

1. **Making changes to the bot?**
   → Edit `fansale_stealth.py` (recommended)
   
2. **Need to understand history?**
   → Read `CHANGELOG.md`
   
3. **Testing login detection?**
   → Run `test_login.py`
   
4. **Need complex features?**
   → Look at `fansale.py` (but prefer stealth version)
   
5. **Old code for reference?**
   → Check `archive/` folder

## Key Principles
- Simpler is more stable
- Stealth > Speed
- Test with 1 browser first
- Clear browser data on 404s
- Manual login is safer