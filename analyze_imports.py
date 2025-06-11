#!/usr/bin/env python3
"""Analyze which installed packages are actually used in the codebase"""

import ast
import os
from pathlib import Path
import subprocess
import sys

def get_imports_from_file(filepath):
    """Extract all imports from a Python file"""
    imports = set()
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except:
        pass
    return imports

def get_all_imports(directories):
    """Get all imports from all Python files in given directories"""
    all_imports = set()
    
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    imports = get_imports_from_file(filepath)
                    all_imports.update(imports)
    
    # Remove relative imports and standard library
    standard_lib = {
        'abc', 'asyncio', 'base64', 'collections', 'concurrent', 'contextlib',
        'dataclasses', 'datetime', 'enum', 'gc', 'hashlib', 'importlib', 'json',
        'logging', 'math', 'os', 'pathlib', 'pickle', 'queue', 'random', 're',
        'shutil', 'signal', 'sqlite3', 'statistics', 'subprocess', 'sys',
        'tempfile', 'threading', 'time', 'traceback', 'tracemalloc', 'typing',
        'unittest', 'urllib', 'uuid', 'weakref', 'webbrowser'
    }
    
    # Filter out standard library and relative imports
    third_party = {imp for imp in all_imports if imp not in standard_lib and not imp.startswith('.')}
    
    return third_party

def get_installed_packages():
    """Get list of installed packages"""
    result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                          capture_output=True, text=True)
    packages = set()
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            package = line.split('==')[0].lower().replace('-', '_')
            packages.add(package)
    return packages

def main():
    # Directories to scan
    dirs_to_scan = ['src', 'tests']
    
    # Get all imports
    print("Analyzing imports in codebase...")
    used_imports = get_all_imports(dirs_to_scan)
    
    # Get installed packages
    print("Getting installed packages...")
    installed = get_installed_packages()
    
    # Map common package names to their pip names
    package_mapping = {
        'yaml': 'pyyaml',
        'pydantic_settings': 'pydantic-settings',
        'email_validator': 'email-validator',
        'flask_socketio': 'flask-socketio',
        'dotenv': 'python-dotenv',
        'playwright_stealth': 'playwright-stealth',
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'msgpack': 'msgpack',
        'zmq': 'pyzmq',
        'nodriver': 'nodriver',
        'jose': 'python-jose',
        'socks': 'python-socks',
        'dateutil': 'python-dateutil',
    }
    
    # Normalize used imports
    normalized_used = set()
    for imp in used_imports:
        normalized = imp.lower().replace('-', '_')
        normalized_used.add(normalized)
        # Add mapped package if exists
        if imp in package_mapping:
            normalized_used.add(package_mapping[imp].lower().replace('-', '_'))
    
    # Find unused packages
    unused = installed - normalized_used
    
    # Remove packages that are dependencies of used packages
    # These are commonly missed but needed
    keep_packages = {
        'typing_extensions', 'certifi', 'charset_normalizer', 'idna', 'urllib3',
        'greenlet', 'pyee', 'six', 'cffi', 'pycparser', 'attrs', 'outcome',
        'sniffio', 'sortedcontainers', 'trio', 'wsproto', 'h11', 'anyio',
        'httpcore', 'pluggy', 'iniconfig', 'packaging', 'frozenlist',
        'multidict', 'yarl', 'aiosignal', 'aiohappyeyeballs', 'annotated_types',
        'pydantic_core', 'typing_inspection', 'uc_micro_py', 'mdurl',
        'markdown_it_py', 'linkify_it_py', 'mdit_py_plugins', 'pygments',
        'websocket_client', 'trio_websocket', 'pyasn1', 'rsa', 'ecdsa',
        'pathspec', 'platformdirs', 'mypy_extensions', 'propcache',
        'colorama', 'dnspython'
    }
    
    unused = unused - keep_packages
    
    # Also check requirements.txt
    print("\nChecking requirements.txt...")
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    print("\n=== ANALYSIS RESULTS ===\n")
    print(f"Total imported packages: {len(normalized_used)}")
    print(f"Total installed packages: {len(installed)}")
    print(f"Potentially unused packages: {len(unused)}")
    
    print("\n=== USED PACKAGES ===")
    for pkg in sorted(normalized_used):
        print(f"  ✓ {pkg}")
    
    print("\n=== POTENTIALLY UNUSED PACKAGES ===")
    unused_in_requirements = []
    for pkg in sorted(unused):
        in_req = any(pkg.replace('_', '-') in requirements or pkg in requirements 
                    for pkg in [pkg, pkg.replace('_', '-')])
        if in_req:
            unused_in_requirements.append(pkg)
        status = "📋 in requirements.txt" if in_req else "❌ not in requirements"
        print(f"  • {pkg} - {status}")
    
    print("\n=== PACKAGES TO REMOVE FROM requirements.txt ===")
    for pkg in unused_in_requirements:
        # Convert back to common package names
        display_name = pkg.replace('_', '-')
        for key, val in package_mapping.items():
            if val.lower().replace('-', '_') == pkg:
                display_name = val
                break
        print(f"  - {display_name}")

if __name__ == "__main__":
    main()