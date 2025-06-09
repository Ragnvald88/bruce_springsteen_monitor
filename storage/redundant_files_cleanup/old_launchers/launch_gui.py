#!/usr/bin/env python3
"""
GUI Launcher for StealthMaster AI v3.0
Ensures proper environment setup before launching the GUI
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the GUI
from src.ui.stealth_gui_v3 import main

if __name__ == "__main__":
    print("🚀 Launching StealthMaster AI v3.0 GUI...")
    main()