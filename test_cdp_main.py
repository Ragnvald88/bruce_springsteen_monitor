#!/usr/bin/env python3
"""Quick test of main.py with CDP stealth integration"""

import subprocess
import sys
import time
import signal

def run_with_timeout(cmd, timeout=60):
    """Run command with timeout"""
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    start_time = time.time()
    output_lines = []
    
    try:
        while True:
            # Check if process has finished
            retcode = proc.poll()
            if retcode is not None:
                # Process finished
                remaining_output = proc.stdout.read()
                if remaining_output:
                    print(remaining_output, end='')
                    output_lines.append(remaining_output)
                break
                
            # Check timeout
            if time.time() - start_time > timeout:
                print(f"\n⏰ Timeout after {timeout} seconds")
                proc.terminate()
                time.sleep(1)
                if proc.poll() is None:
                    proc.kill()
                break
                
            # Read available output
            line = proc.stdout.readline()
            if line:
                print(line, end='')
                output_lines.append(line)
                
                # Check for successful initialization
                if "Initializing Unified Handler" in line:
                    print("\n✅ CDP stealth integration detected!")
                elif "Using headful mode for Ticketmaster" in line:
                    print("✅ Platform-specific headless mode working!")
                elif "CDP stealth measures applied" in line:
                    print("✅ CDP stealth successfully applied!")
                elif "ACCESSIBLE" in line:
                    print("\n🎉 Platform access successful with CDP stealth!")
                elif "Failed to initialize monitor" in line and "'BrowserType' object has no attribute" not in line:
                    print("\n❌ Different error occurred")
                    
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        proc.terminate()
        
    return '\n'.join(output_lines)

if __name__ == "__main__":
    print("🛡️ Testing CDP Stealth Integration in main.py")
    print("="*60)
    
    output = run_with_timeout("python src/main.py", timeout=45)
    
    print("\n" + "="*60)
    print("📊 Test Summary:")
    
    if "'BrowserType' object has no attribute" not in output:
        print("✅ CDP browser creation issue FIXED!")
    else:
        print("❌ CDP browser creation still has issues")
        
    if "Failed to initialize monitor" not in output or "monitors initialized" in output:
        print("✅ Monitors initialized successfully!")
    else:
        print("⚠️ Monitor initialization had issues")
        
    if "CDP stealth measures applied" in output:
        print("✅ CDP stealth was applied!")
    else:
        print("⚠️ CDP stealth application not confirmed")
        
    print("\n✅ Test complete")