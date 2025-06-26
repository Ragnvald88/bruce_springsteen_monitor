#!/usr/bin/env python3
"""
Chrome Process Cleanup Script
Kills stuck Chrome processes that prevent bot from starting
"""

import subprocess
import sys
import time

def kill_chrome_processes():
    """Kill all Chrome and ChromeDriver processes"""
    print("🧹 Chrome Process Cleanup")
    print("=" * 50)
    
    processes_to_kill = [
        "Google Chrome",
        "Google Chrome Helper",
        "Google Chrome Helper (Renderer)",
        "Google Chrome Helper (GPU)",
        "chromedriver",
        "ChromeDriver",
    ]
    
    killed_count = 0
    
    for process_name in processes_to_kill:
        try:
            # Use pkill for macOS/Linux
            if sys.platform != "win32":
                result = subprocess.run(
                    ["pkill", "-f", process_name],
                    capture_output=True
                )
                if result.returncode == 0:
                    print(f"✅ Killed {process_name} processes")
                    killed_count += 1
            else:
                # Use taskkill for Windows
                subprocess.run(
                    ["taskkill", "/F", "/IM", f"{process_name}.exe"],
                    capture_output=True
                )
        except:
            pass
    
    if killed_count > 0:
        print(f"\n✅ Cleaned up {killed_count} process types")
        print("⏳ Waiting 3 seconds for processes to fully terminate...")
        time.sleep(3)
    else:
        print("✅ No Chrome processes found to clean")
    
    # Also clean up any orphaned browser profiles
    try:
        import shutil
        from pathlib import Path
        
        profile_dir = Path("browser_profiles")
        if profile_dir.exists():
            # Check for lock files
            lock_files = list(profile_dir.glob("*/SingletonLock"))
            if lock_files:
                print(f"\n🔒 Found {len(lock_files)} locked browser profiles")
                for lock_file in lock_files:
                    try:
                        lock_file.unlink()
                        print(f"   ✓ Removed lock: {lock_file.parent.name}")
                    except:
                        pass
    except:
        pass
    
    print("\n✅ Cleanup complete! You can now run the bot.")

if __name__ == "__main__":
    kill_chrome_processes()
