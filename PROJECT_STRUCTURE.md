# StealthMaster Project Structure

## Active Files (Focus Here)
```
├── fansale_no_login.py    # ⭐ MAIN BOT - No login required! (357 lines)
├── fansale_stealth.py     # Previous version - requires login (495 lines)
├── fansale.py             # Original full version (1151 lines, complex)
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
   → Edit `fansale_no_login.py` (no login required!)
   
2. **Need login functionality?**
   → Use `fansale_stealth.py` or `fansale.py`
   
3. **Need to understand history?**
   → Read `CHANGELOG.md`
   
4. **Testing login detection?**
   → Run `test_login.py`
   
5. **Old code for reference?**
   → Check `archive/` folder

## Key Principles
- Simpler is more stable
- Stealth > Speed
- Test with 1 browser first
- Clear browser data on 404s
- Manual login is safer