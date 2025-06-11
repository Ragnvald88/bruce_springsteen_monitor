#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing StealthMaster imports...")

try:
    from src.main import StealthMaster
    print("✓ Main module imported")
except Exception as e:
    print(f"✗ Main module failed: {e}")

try:
    from src.config import Settings, load_settings
    print("✓ Config module imported")
except Exception as e:
    print(f"✗ Config module failed: {e}")

try:
    from src.browser.launcher import launcher
    print("✓ Browser launcher imported")
except Exception as e:
    print(f"✗ Browser launcher failed: {e}")

try:
    from src.ui.enhanced_dashboard import EnhancedDashboard
    print("✓ Enhanced dashboard imported")
except Exception as e:
    print(f"✗ Enhanced dashboard failed: {e}")

try:
    from src.ui.modern_dashboard import ModernDashboard
    print("✓ Modern dashboard imported")
except Exception as e:
    print(f"✗ Modern dashboard failed: {e}")

try:
    from src.database.statistics import stats_manager
    print("✓ Statistics manager imported")
except Exception as e:
    print(f"✗ Statistics manager failed: {e}")

try:
    from src.stealth.nodriver_core import nodriver_core
    print("✓ Nodriver core imported")
except Exception as e:
    print(f"✗ Nodriver core failed: {e}")

print("\nAll imports completed!")