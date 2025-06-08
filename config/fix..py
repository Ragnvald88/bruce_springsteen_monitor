#!/usr/bin/env python3
"""
StealthMaster AI - Quick Fix for Import Errors
Run this from your project root to fix all import issues
"""

import os
import re
from pathlib import Path

def fix_imports():
    """Fix all import errors in the project"""
    
    print("🔧 StealthMaster AI Import Fixer\n")
    
    # Fix 1: Update main.py to use correct orchestrator
    main_path = Path("src/main.py")
    if main_path.exists():
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Fix orchestrator import
        if "from src.core.orchestrator import" in content:
            content = content.replace(
                "from src.core.orchestrator import UltimateOrchestrator",
                "from src.core.orchestrator_v2 import UltimateOrchestrator"
            )
            with open(main_path, 'w') as f:
                f.write(content)
            print("✅ Fixed main.py orchestrator import")
    
    # Fix 2: Fix typo in utils.py
    utils_path = Path("src/profiles/utils.py")
    if utils_path.exists():
        with open(utils_path, 'r') as f:
            content = f.read()
        
        # Fix typo
        content = content.replace("consilidated_models", "consolidated_models")
        
        # If consolidated_models doesn't exist, use regular models
        if not Path("src/profiles/consolidated_models.py").exists():
            print("⚠️  consolidated_models.py not found, updating imports...")
            content = re.sub(
                r'from [\.]*consolidated_models import.*',
                'from .models import BrowserProfile\nfrom ..core.enums import PlatformType as Platform',
                content
            )
        
        with open(utils_path, 'w') as f:
            f.write(content)
        print("✅ Fixed utils.py imports")
    
    # Fix 3: Update enums.py to not depend on consolidated_models
    enums_path = Path("src/core/enums.py")
    if enums_path.exists():
        print("📝 Creating clean enums.py...")
        
        clean_enums = '''# src/core/enums.py
from enum import Enum, auto

class OperationMode(Enum):
    """System operation modes"""
    STEALTH = "stealth"
    BEAST = "beast"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    ULTRA_STEALTH = "ultra_stealth"

class PlatformType(Enum):
    """Supported ticketing platforms"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"

class PriorityLevel(Enum):
    """Priority levels with multipliers"""
    CRITICAL = (1, 1.0, 0.1)
    HIGH = (2, 0.8, 0.3)
    NORMAL = (3, 0.6, 0.5)
    LOW = (4, 0.4, 0.8)
    
    @property
    def numeric_value(self):
        return self.value[0]
    
    @property
    def speed_multiplier(self):
        return self.value[1]
    
    @property
    def data_multiplier(self):
        return self.value[2]

class DetectionStatus(Enum):
    """Detection states"""
    MONITORING = auto()
    DETECTED = auto()
    VERIFIED = auto()
    ATTEMPTING = auto()
    SUCCESS = auto()
    FAILED = auto()
    BLOCKED = auto()
    RATE_LIMITED = auto()
'''
        
        with open(enums_path, 'w') as f:
            f.write(clean_enums)
        print("✅ Created clean enums.py")
    
    # Fix 4: Check if orchestrator.py exists (should be orchestrator_v2.py)
    old_orch = Path("src/core/orchestrator.py")
    new_orch = Path("src/core/orchestrator_v2.py")
    
    if old_orch.exists() and not new_orch.exists():
        print("\n⚠️  You have orchestrator.py but need orchestrator_v2.py!")
        print("   Either:")
        print("   1. Add orchestrator_v2.py from the artifacts")
        print("   2. Rename orchestrator.py to orchestrator_v2.py")
    
    # Fix 5: Create missing __init__.py files
    init_files = [
        "src/__init__.py",
        "src/core/__init__.py",
        "src/profiles/__init__.py",
        "src/platforms/__init__.py"
    ]
    
    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"✅ Created {init_file}")
    
    print("\n✨ Import fixes complete!")
    print("\nNext steps:")
    print("1. Make sure you have orchestrator_v2.py (not orchestrator.py)")
    print("2. Add the new StealthMaster files from artifacts")
    print("3. Run: python src/main.py")

if __name__ == "__main__":
    fix_imports()