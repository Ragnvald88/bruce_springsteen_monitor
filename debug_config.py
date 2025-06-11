#!/usr/bin/env python3
"""Debug config loading."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.config import load_settings
    print("✓ Config module imported")
    
    settings = load_settings()
    print(f"✓ Settings loaded")
    print(f"  Targets in config: {len(settings.targets)}")
    
    for i, target in enumerate(settings.targets):
        print(f"\nTarget {i+1}:")
        print(f"  Platform: {target.platform}")
        print(f"  Event: {target.event_name}")
        print(f"  Enabled: {target.enabled}")
        print(f"  Priority: {target.priority}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()