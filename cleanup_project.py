#!/usr/bin/env python3
"""
Cleanup script to organize the FanSale bot project
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """Clean up and organize project files"""
    
    # Files to archive (not used in final solution)
    files_to_archive = [
        "fansale_bot_basic.py",
        "fansale_bot_fixed.py", 
        "fansale_hybrid_ultimate.py",
        "fansale_final_backup.py",
        "fansale_final_v2.py",
        "fansale_optimal.py",
        "fansale_sniper_ultimate.py",
        "fansale_sniper_v4_PRO.py",
        "elite_fansale_sniper.py"
    ]
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = Path(f"archive/cleanup_{timestamp}")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Archive old files
    archived_count = 0
    for filename in files_to_archive:
        file_path = Path(filename)
        if file_path.exists():
            shutil.move(str(file_path), str(archive_dir / filename))
            print(f"✓ Archived: {filename}")
            archived_count += 1
        
        # Also check in archive directory
        archive_path = Path("archive") / filename
        if archive_path.exists():
            shutil.move(str(archive_path), str(archive_dir / filename))
            print(f"✓ Archived: archive/{filename}")
            archived_count += 1
    
    # Remove empty directories
    for dir_path in ["archive/old_versions", "archive/test_files"]:
        if Path(dir_path).exists() and not any(Path(dir_path).iterdir()):
            Path(dir_path).rmdir()
            print(f"✓ Removed empty directory: {dir_path}")
    
    print(f"\n✅ Cleanup complete! Archived {archived_count} files")
    print(f"📁 Archive location: {archive_dir}")
    
    # List remaining key files
    print("\n📋 Active files:")
    key_files = [
        "fansale_bot.py",
        "fansale_sensor_bot.py", 
        "fansale_advanced.py",
        "test_akamai_pattern.py",
        "DETECTIVE_REPORT_403.md",
        "SOLUTION_SUMMARY.md"
    ]
    
    for filename in key_files:
        if Path(filename).exists():
            print(f"  ✓ {filename}")

if __name__ == "__main__":
    cleanup_project()
