#!/usr/bin/env python3
"""
Cleanup script to archive old files
"""

import shutil
from pathlib import Path
from datetime import datetime

def cleanup():
    """Archive old scripts"""
    print("🧹 Cleaning up old scripts...")
    
    # Files to archive
    old_files = [
        "fansale_bot.py",
        "fansale_simple_browser.py",
        "fansale_lite_browser.py",
        "fansale_parallel_bot.py",
        "fansale_multi_browser.py",
        "test_akamai_pattern.py",
        "CLEANUP_SUMMARY.md",
        "PARALLEL_STRATEGY.md",
        "PROXY_DATA_GUIDE.md",
        "README_REALISTIC.md"
    ]
    
    # Create archive directory
    archive_dir = Path("archive") / f"old_scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Move old files
    archived = 0
    for file in old_files:
        if Path(file).exists():
            shutil.move(file, str(archive_dir / file))
            print(f"  ✓ Archived: {file}")
            archived += 1
    
    # Clean up empty directories
    for dir_name in ["logs", "session", "data", "utilities", "docs", "config"]:
        dir_path = Path(dir_name)
        if dir_path.exists() and not any(dir_path.iterdir()):
            dir_path.rmdir()
            print(f"  ✓ Removed empty directory: {dir_name}")
    
    print(f"\n✅ Archived {archived} files")
    print("✅ Project now uses single unified script: fansale.py")

if __name__ == "__main__":
    cleanup()
