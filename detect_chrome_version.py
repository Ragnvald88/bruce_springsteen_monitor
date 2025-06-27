#!/usr/bin/env python3
"""Detect installed Chrome version"""
import subprocess
import platform
import re

def get_chrome_version():
    """Detect Chrome version on different platforms"""
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            # Try different Chrome locations
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome"
            ]
            
            for path in chrome_paths:
                try:
                    result = subprocess.run(
                        [path.replace("~", "/Users/" + subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip()), "--version"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        version_match = re.search(r'(\d+)\.', result.stdout)
                        if version_match:
                            return int(version_match.group(1))
                except:
                    continue
                    
        elif system == "Windows":
            # Windows Chrome paths
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                version_match = re.search(r'(\d+)\.', version)
                if version_match:
                    return int(version_match.group(1))
            except:
                pass
                
        elif system == "Linux":
            # Linux Chrome
            result = subprocess.run(
                ["google-chrome", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version_match = re.search(r'(\d+)\.', result.stdout)
                if version_match:
                    return int(version_match.group(1))
                    
    except Exception as e:
        print(f"Error detecting Chrome version: {e}")
    
    return None

def main():
    """Main function"""
    print("🔍 Chrome Version Detector")
    print("=" * 40)
    
    version = get_chrome_version()
    
    if version:
        print(f"✅ Chrome version detected: {version}")
        print(f"\nAdd this to your script:")
        print(f"CHROME_VERSION = {version}")
    else:
        print("❌ Could not detect Chrome version")
        print("\nTry running:")
        if platform.system() == "Darwin":
            print('"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version')
        elif platform.system() == "Windows":
            print('"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --version')
        elif platform.system() == "Linux":
            print("google-chrome --version")

if __name__ == "__main__":
    main()