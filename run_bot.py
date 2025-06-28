#!/usr/bin/env python3
"""
Quick launcher for FanSale Ultimate Bot
Handles Python 3.13 compatibility automatically
"""

import subprocess
import sys
import os

# Ensure we're using the venv Python
venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
if os.path.exists(venv_python):
    python_cmd = venv_python
else:
    python_cmd = sys.executable

print("🚀 FanSale Ultimate Bot Launcher")
print("=" * 50)

# Check if distutils fix is needed
try:
    import distutils.version
except ImportError:
    print("⚠️  Python 3.13 detected, applying compatibility fix...")
    # Create minimal distutils compatibility
    import site
    site_packages = site.getsitepackages()[0]
    distutils_path = os.path.join(site_packages, "distutils")
    
    if not os.path.exists(distutils_path):
        os.makedirs(distutils_path)
        with open(os.path.join(distutils_path, "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(distutils_path, "version.py"), "w") as f:
            f.write("""class LooseVersion:
    def __init__(self, vstring):
        self.vstring = str(vstring)
        self.version = self._parse(vstring)
    def _parse(self, vstring):
        components = []
        for part in str(vstring).split('.'):
            try:
                components.append(int(part))
            except ValueError:
                components.append(part)
        return components
    def __str__(self):
        return self.vstring
    def __eq__(self, other):
        return self.version == self._coerce(other).version
    def __lt__(self, other):
        return self.version < self._coerce(other).version
    def _coerce(self, other):
        if isinstance(other, LooseVersion):
            return other
        return LooseVersion(other)
""")
    print("")

# Run the bot
try:
    print("\n🎯 Launching FanSale Ultimate Bot...")
    print("=" * 50)
    subprocess.run([python_cmd, 'fansale_ultimate.py'])
except KeyboardInterrupt:
    print("\n\n👋 Bot stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")