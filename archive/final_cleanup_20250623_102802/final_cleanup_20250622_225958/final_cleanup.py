#!/usr/bin/env python3
"""
Final cleanup script - Remove redundant files after optimal solution found
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def final_cleanup():
    """Remove redundant scripts now that we have the optimal solution"""
    
    print("🧹 Final StealthMaster Cleanup")
    print("=" * 50)
    
    # Create final archive directory
    archive_dir = Path("archive") / f"final_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to remove (with reasons)
    files_to_remove = {
        # Flawed/Over-engineered Bot Scripts
        "elite_fansale_sniper.py": "Incomplete, never finished",
        "elite_hybrid_sniper.py": "Fatal flaw - no server refresh",
        "fansale_sniper_ultimate.py": "Over-engineered, too complex",
        "fansale_sniper_v4_PRO.py": "Good logic, but superseded by final version",
        "fansale_optimal.py": "FLAWED timing - sleeps before refresh!",
        
        # Outdated Documentation
        "ELITE_STRATEGY.md": "Promotes flawed client-side approach",
        "README_ELITE.md": "Outdated strategy",
        "IMPROVEMENTS_ANALYSIS.md": "Compares outdated versions",
        
        # One-time Use Scripts
        "cleanup_and_organize.py": "Already executed",
        "save_revised_script.py": "Already executed",
        "data_usage_calculator.py": "Made its point, not needed anymore",
        
        # Outdated Configs
        "config_ultimate.yaml": "For removed ultimate script",
        
        # Old logs
        "fansale_monitor.log": "Old log file"
    }
    
    print("\n📁 Archiving redundant files:")
    removed_count = 0
    
    for filename, reason in files_to_remove.items():
        file_path = Path(filename)
        if file_path.exists():
            try:
                # Archive it
                dest_path = archive_dir / filename
                shutil.move(str(file_path), str(dest_path))
                print(f"  ✓ {filename}")
                print(f"    → Reason: {reason}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ {filename}: {e}")
    
    print(f"\n📊 Archived {removed_count} files to: {archive_dir}")
    
    # What remains
    print("\n✅ Clean project structure:")
    print("""
    stealthmaster/
    ├── fansale_final.py       # THE WINNER - Correct timing!
    ├── test_chrome_performance.py  # Useful for testing
    ├── requirements.txt        # Dependencies
    ├── config.yaml            # Configuration
    ├── .env                   # Your credentials
    ├── README.md              # Project docs
    ├── utilities/             # Useful modules (notifications, etc)
    ├── browser_profiles/      # Session persistence
    ├── logs/                  # Runtime logs
    └── archive/               # Old versions (just in case)
    """)
    
    # Create updated README
    create_final_readme()
    
    print("\n🎯 Project is now clean and focused!")
    print("Run: python3 fansale_final.py")

def create_final_readme():
    """Create the final, simple README"""
    readme_content = """# FanSale Ticket Bot - FINAL Version

A simple, effective ticket bot for FanSale.it with CORRECT timing logic.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `.env`:**
   ```
   FANSALE_EMAIL="your_email@example.com"
   FANSALE_PASSWORD="your_password"
   
   # IPRoyal Proxy (optional but recommended)
   IPROYAL_USERNAME="your_username"
   IPROYAL_PASSWORD="your_password"
   IPROYAL_HOSTNAME="geo.iproyal.com"
   IPROYAL_PORT="12321"
   ```

3. **Set target URL in `config.yaml`**

4. **Run:**
   ```bash
   python3 fansale_final.py
   ```

## Why This Works

- **Correct Timing**: Refreshes FIRST, then waits (never blind to new tickets)
- **Smart Patterns**: Human-like timing to avoid detection
- **Bandwidth Efficient**: Aggressively blocks images/ads to save proxy data
- **Battle-tested**: Based on proven scraping patterns

## The Critical Difference

❌ WRONG: Check → Wait → Refresh (gives competitors time!)
✅ RIGHT: Check → Refresh → Wait (see new tickets instantly!)

## Features

- ✅ Automatic login with session persistence
- ✅ Human-like patterns (applied AFTER refresh)
- ✅ Aggressive bandwidth optimization
- ✅ Micro-optimized purchase flow
- ✅ Simple, maintainable code

Good luck getting those tickets! 🎫
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("📝 Updated README.md with final documentation")

if __name__ == "__main__":
    response = input("\n⚠️  This will archive many scripts. Continue? (y/n): ")
    if response.lower() == 'y':
        final_cleanup()
    else:
        print("Cleanup cancelled.")
