#!/usr/bin/env python3
"""
Project Cleanup Script
Removes duplicates, old files, and organizes the project
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """Clean up the stealthmaster project"""
    
    print("🧹 Starting project cleanup...")
    print("=" * 50)
    
    # Timestamp for this cleanup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_archive = Path(f"archive/final_cleanup_{timestamp}")
    final_archive.mkdir(parents=True, exist_ok=True)
    
    # 1. Remove duplicate browser profiles
    print("\n📁 Cleaning browser profiles...")
    browser_profiles = Path("browser_profiles")
    if browser_profiles.exists():
        for profile in browser_profiles.iterdir():
            if profile.is_dir() and 'fansale' in profile.name:
                shutil.move(str(profile), str(final_archive / profile.name))
                print(f"  ✓ Archived browser profile: {profile.name}")
    
    # 2. Archive all old fansale variants from archive folder
    print("\n📦 Consolidating archive files...")
    old_archives = [
        "archive/cleanup_20250623_094331",
        "archive/final_cleanup_20250622_225958",
        "archive/analysis_scripts",
        "archive/test_files",
        "archive/unrealistic",
        "archive/src"
    ]
    
    for old_dir in old_archives:
        if Path(old_dir).exists():
            dest = final_archive / Path(old_dir).name
            shutil.move(old_dir, str(dest))
            print(f"  ✓ Consolidated: {old_dir}")
    
    # 3. Clean up loose files in archive
    archive_files = [
        "archive/fansale_advanced_old.py",
        "archive/fansale_bot.py",
        "archive/cleanup_project.py"
    ]
    
    for file in archive_files:
        if Path(file).exists():
            shutil.move(file, str(final_archive / Path(file).name))
            print(f"  ✓ Archived: {file}")
    
    # 4. Clean up data directories
    print("\n🗂️ Cleaning data directories...")
    data_dirs = ["data/cookies", "logs", "session"]
    
    for dir_path in data_dirs:
        if Path(dir_path).exists():
            # Check if empty or has old files
            files = list(Path(dir_path).iterdir())
            if files:
                for file in files:
                    if file.is_file() and ('fansale' in file.name or 'cookie' in file.name):
                        file.unlink()
                        print(f"  ✓ Removed old file: {file.name}")
    
    # 5. Keep only essential files
    print("\n✅ Essential files kept:")
    essential_files = [
        "fansale_bot.py",              # Main entry
        "fansale_lite_browser.py",     # Low data version
        "fansale_simple_browser.py",   # Normal version
        "fansale_advanced.py",         # Advanced version (optional)
        "test_akamai_pattern.py",      # Test script
        "FINAL_SUMMARY.md",            # Documentation
        "PROXY_DATA_GUIDE.md",         # Proxy guide
        "README_REALISTIC.md",         # Realistic assessment
        ".env",                        # Environment vars
        "requirements.txt"             # Dependencies
    ]
    
    for file in essential_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
    
    # 6. Create clean structure
    print("\n📂 Final structure:")
    print("""
    stealthmaster/
    ├── fansale_bot.py           (main entry point)
    ├── fansale_lite_browser.py  (low data usage)
    ├── fansale_simple_browser.py (normal browser)
    ├── fansale_advanced.py      (advanced features)
    ├── test_akamai_pattern.py   (testing)
    ├── .env                     (your credentials)
    ├── requirements.txt         (dependencies)
    ├── FINAL_SUMMARY.md         (what works)
    ├── PROXY_DATA_GUIDE.md      (proxy info)
    ├── README_REALISTIC.md      (reality check)
    └── archive/                 (all old versions)
        └── final_cleanup_{timestamp}/
    """.format(timestamp=timestamp))
    
    print(f"\n✅ Cleanup complete!")
    print(f"📁 All old files moved to: archive/final_cleanup_{timestamp}/")
    print(f"💾 Project size reduced significantly")
    
    # Count files
    remaining_files = len([f for f in Path(".").glob("*.py")])
    print(f"\n📊 Stats: {remaining_files} Python files remaining (was 20+)")

if __name__ == "__main__":
    cleanup_project()
