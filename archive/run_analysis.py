#!/usr/bin/env python3
"""
Run the analysis to see what's being detected
"""

import subprocess
import os

print("🔍 Running detection analysis...")
print("=" * 50)
print("\nThis will help identify why you're being blocked.\n")

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the analysis
subprocess.run([
    "python3", 
    "analyze_detection.py"
])
