#!/usr/bin/env python3
"""
Resource cleanup utility for StealthMaster
Keeps the project lean and efficient
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

def clean_browser_profiles(days_old=7):
    """Remove browser profiles older than specified days"""
    profiles_dir = Path("browser_profiles")
    if not profiles_dir.exists():
        return 0
    
    cleaned = 0
    for profile in profiles_dir.iterdir():
        if profile.is_dir():
            # Check modification time
            mtime = datetime.fromtimestamp(profile.stat().st_mtime)
            if datetime.now() - mtime > timedelta(days=days_old):
                try:
                    shutil.rmtree(profile)
                    cleaned += 1
                    print(f"✅ Removed old profile: {profile.name}")
                except Exception as e:
                    print(f"❌ Failed to remove {profile.name}: {e}")
    
    return cleaned

def rotate_screenshots(keep_last=10):
    """Keep only the most recent screenshots"""
    screenshots_dir = Path("screenshots")
    if not screenshots_dir.exists():
        return 0
    
    # Get all screenshots sorted by modification time
    screenshots = sorted(
        screenshots_dir.glob("*.png"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # Remove older screenshots
    removed = 0
    for screenshot in screenshots[keep_last:]:
        try:
            screenshot.unlink()
            removed += 1
        except Exception as e:
            print(f"❌ Failed to remove {screenshot.name}: {e}")
    
    if removed:
        print(f"✅ Removed {removed} old screenshots")
    
    return removed

def compress_logs(max_size_mb=1):
    """Compress log files if they exceed max size"""
    import gzip
    
    log_files = ["fansale_bot.log", "debug.log"]
    compressed = 0
    
    for log_file in log_files:
        log_path = Path(log_file)
        if not log_path.exists():
            continue
        
        # Check size
        size_mb = log_path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            # Create compressed backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"logs/{log_path.stem}_{timestamp}.gz"
            
            # Create logs directory
            Path("logs").mkdir(exist_ok=True)
            
            try:
                with open(log_path, 'rb') as f_in:
                    with gzip.open(backup_name, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Clear original log
                with open(log_path, 'w') as f:
                    f.write(f"Log rotated on {datetime.now()}\n")
                
                print(f"✅ Compressed {log_file} ({size_mb:.1f}MB) to {backup_name}")
                compressed += 1
            except Exception as e:
                print(f"❌ Failed to compress {log_file}: {e}")
    
    return compressed

def clean_project():
    """Main cleanup function"""
    print("🧹 StealthMaster Cleanup Utility")
    print("="*40)
    
    # Clean browser profiles
    print("\n📁 Cleaning browser profiles...")
    profiles_cleaned = clean_browser_profiles(days_old=7)
    
    # Rotate screenshots
    print("\n📸 Rotating screenshots...")
    screenshots_removed = rotate_screenshots(keep_last=10)
    
    # Compress logs
    print("\n📄 Checking log files...")
    logs_compressed = compress_logs(max_size_mb=1)
    
    # Clean pycache
    print("\n🗑️ Cleaning Python cache...")
    pycache_cleaned = 0
    pycache_dirs = list(Path(".").rglob("__pycache__"))
    for pycache in pycache_dirs:
        try:
            shutil.rmtree(pycache)
            pycache_cleaned += 1
        except:
            pass
    
    print(f"\n✨ Cleanup complete!")
    print(f"   • Browser profiles cleaned: {profiles_cleaned}")
    print(f"   • Screenshots removed: {screenshots_removed}")
    print(f"   • Logs compressed: {logs_compressed}")
    print(f"   • Python cache cleaned: {pycache_cleaned}")

if __name__ == "__main__":
    clean_project()
