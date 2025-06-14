#!/usr/bin/env python3
"""
StealthMaster GUI Launcher - Enhanced Version
Handles all startup scenarios gracefully
"""

import sys
import os
import subprocess
from pathlib import Path
import traceback

def check_requirements():
    """Check and install missing requirements"""
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import pyqtgraph
    except ImportError:
        missing_deps.append("pyqtgraph")
    
    try:
        import aiofiles
    except ImportError:
        missing_deps.append("aiofiles")
    
    if missing_deps:
        print(f"Missing requirements: {', '.join(missing_deps)}")
        print("Installing GUI requirements...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "PyQt6", "pyqtgraph", "aiofiles"
            ])
            print("✅ Requirements installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    
    return True

def launch_gui():
    """Launch GUI with proper error handling"""
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Set environment
    os.environ['STEALTHMASTER_GUI'] = '1'
    
    try:
        # Check requirements first
        if not check_requirements():
            print("\n❌ Could not install required dependencies.")
            print("Please install manually with: pip install PyQt6 pyqtgraph aiofiles")
            return False
        
        # Import and launch
        from src.ui.advanced_gui import main
        main()
        return True
        
    except ImportError as e:
        # More specific error handling
        print(f"\n❌ Import Error: {e}")
        
        if "PyQt6" in str(e):
            print("\nPyQt6 is not properly installed.")
            print("Try: pip install PyQt6")
        elif "advanced_gui" in str(e):
            print("\nGUI module not found. Make sure src/ui/advanced_gui.py exists.")
        else:
            print("\nUnknown import error. Check your Python environment.")
        
        print(f"\nDebug info:\n{traceback.format_exc()}")
        return False
        
    except Exception as e:
        # General error handling
        print(f"\n❌ GUI Launch Failed: {e}")
        print(f"\nDebug info:\n{traceback.format_exc()}")
        return False

def launch_cli_fallback():
    """Launch CLI version as fallback"""
    print("\n🔄 Falling back to CLI mode...")
    
    try:
        # Import main CLI entry point
        from stealthmaster import main as cli_main
        import asyncio
        asyncio.run(cli_main())
    except Exception as e:
        print(f"\n❌ CLI launch also failed: {e}")
        print("\nPlease check your installation and try again.")

if __name__ == "__main__":
    # Try to launch GUI
    if not launch_gui():
        # Ask user if they want to use CLI instead
        print("\n" + "="*50)
        response = input("Would you like to start in CLI mode instead? (y/n): ").lower().strip()
        
        if response == 'y':
            launch_cli_fallback()
        else:
            print("\nExiting. Please fix the issues and try again.")
            sys.exit(1)
