#!/usr/bin/env python3
"""
Fix for Python 3.13 compatibility issues with undetected-chromedriver
"""

import subprocess
import sys
import os

def fix_dependencies():
    """Fix dependency issues for Python 3.13"""
    
    print("🔧 Fixing StealthMaster dependencies for Python 3.13...")
    print("=" * 50)
    
    venv_python = "/Users/macbookpro_ronald/Documents/Personal/Projects/stealthmaster/venv/bin/python"
    venv_pip = "/Users/macbookpro_ronald/Documents/Personal/Projects/stealthmaster/venv/bin/pip"
    
    # Step 1: Upgrade pip
    print("\n📦 Upgrading pip...")
    subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    # Step 2: Install/upgrade setuptools
    print("\n📦 Installing setuptools...")
    subprocess.run([venv_pip, "install", "--upgrade", "setuptools"], check=True)
    
    # Step 3: Create a compatibility patch for distutils
    print("\n🔧 Creating distutils compatibility patch...")
    
    # Find site-packages directory
    site_packages = subprocess.check_output(
        [venv_python, "-c", "import site; print(site.getsitepackages()[0])"],
        text=True
    ).strip()
    
    # Create distutils compatibility module
    distutils_path = os.path.join(site_packages, "distutils")
    os.makedirs(distutils_path, exist_ok=True)
    
    # Create __init__.py
    with open(os.path.join(distutils_path, "__init__.py"), "w") as f:
        f.write("# Compatibility shim for Python 3.13\n")
    
    # Create version.py with LooseVersion
    version_content = '''"""Compatibility shim for distutils.version"""

class LooseVersion:
    """Simplified version comparison for compatibility"""
    def __init__(self, vstring=None):
        self.vstring = vstring or ""
        self.version = self._parse(vstring)
    
    def _parse(self, vstring):
        if not vstring:
            return []
        parts = []
        for part in vstring.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(part)
        return parts
    
    def __str__(self):
        return self.vstring
    
    def __repr__(self):
        return f"LooseVersion('{self.vstring}')"
    
    def __eq__(self, other):
        return self.version == other.version
    
    def __lt__(self, other):
        return self.version < other.version
    
    def __le__(self, other):
        return self.version <= other.version
    
    def __gt__(self, other):
        return self.version > other.version
    
    def __ge__(self, other):
        return self.version >= other.version
'''
    
    with open(os.path.join(distutils_path, "version.py"), "w") as f:
        f.write(version_content)
    
    print("✅ Distutils compatibility patch created!")
    
    # Step 4: Reinstall undetected-chromedriver
    print("\n📦 Reinstalling undetected-chromedriver...")
    subprocess.run([venv_pip, "uninstall", "-y", "undetected-chromedriver"], check=False)
    subprocess.run([venv_pip, "install", "undetected-chromedriver>=3.5.5"], check=True)
    
    # Step 5: Install other dependencies
    print("\n📦 Installing other dependencies...")
    dependencies = [
        "selenium-wire",
        "selenium>=4.0.0",
        "python-dotenv",
        "PyYAML",
        "requests",
        "colorlog"
    ]
    
    for dep in dependencies:
        subprocess.run([venv_pip, "install", dep], check=True)
    
    # Test import
    print("\n🧪 Testing imports...")
    try:
        subprocess.run(
            [venv_python, "-c", "import undetected_chromedriver as uc; print('✅ Success!')"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("❌ Import test failed")
        return False
    
    print("\n✅ All dependencies fixed!")
    print(f"🎯 Run: {venv_python} fansale_final.py")
    return True

if __name__ == "__main__":
    success = fix_dependencies()
    sys.exit(0 if success else 1)
