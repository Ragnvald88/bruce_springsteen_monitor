#!/usr/bin/env python3
"""Fix duplicate class definitions across the project."""

import os
import re
from pathlib import Path

# Define the duplicate classes and their canonical locations
DUPLICATE_FIXES = {
    'DetectionType': {
        'keep': 'src/constants.py',
        'remove_from': ['src/detection/monitor.py', 'src/detection/recovery.py', 'src/detection/adaptive_response.py']
    },
    'ProfileStatus': {
        'keep': 'src/constants.py',
        'remove_from': ['src/profiles/models.py']
    },
    'MonitoringLevel': {
        'keep': 'src/detection/monitor.py',
        'remove_from': ['src/config.py']
    },
    'SessionState': {
        'keep': 'src/network/session.py',
        'remove_from': ['src/profiles/persistence.py']
    },
    'TLSProfile': {
        'keep': 'src/network/tls_fingerprint.py',
        'remove_from': ['src/stealth/tls_randomizer.py']
    },
    'DataUsageMetrics': {
        'keep': 'src/telemetry/data_tracker.py',
        'remove_from': ['src/browser/pool.py']
    },
    'DetectionEvent': {
        'keep': 'src/detection/monitor.py',
        'remove_from': ['src/detection/adaptive_response.py']
    }
}

def fix_imports_in_file(file_path, class_name, canonical_import):
    """Update imports to use the canonical location."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update the import if the class is used
    if class_name in content:
        # Add the import if not present
        if canonical_import not in content:
            # Find the import section
            import_section_end = 0
            for i, line in enumerate(content.split('\n')):
                if line.strip() and not line.startswith(('import', 'from', '#')) and import_section_end == 0:
                    import_section_end = i
                    break
            
            lines = content.split('\n')
            lines.insert(import_section_end - 1, canonical_import)
            content = '\n'.join(lines)
            
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Added import to {file_path}")

def remove_duplicate_class(file_path, class_name):
    """Remove duplicate class definition from file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    in_class = False
    class_indent = 0
    new_lines = []
    removed = False
    
    for i, line in enumerate(lines):
        # Check if we're starting the duplicate class
        if f'class {class_name}' in line and not in_class:
            in_class = True
            class_indent = len(line) - len(line.lstrip())
            removed = True
            continue
        
        # Check if we're still in the class
        if in_class:
            current_indent = len(line) - len(line.lstrip())
            # If we hit a line with same or less indentation (and it's not empty), we're out of the class
            if line.strip() and current_indent <= class_indent:
                in_class = False
            else:
                continue  # Skip lines that are part of the class
        
        new_lines.append(line)
    
    if removed:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print(f"Removed {class_name} from {file_path}")
        
        # Generate the canonical import
        canonical_file = DUPLICATE_FIXES[class_name]['keep']
        module_path = canonical_file.replace('src/', '').replace('.py', '').replace('/', '.')
        canonical_import = f"from ..{module_path} import {class_name}"
        
        # Fix imports
        fix_imports_in_file(file_path, class_name, canonical_import)

def main():
    """Fix all duplicate class definitions."""
    root = Path(__file__).parent
    
    for class_name, locations in DUPLICATE_FIXES.items():
        print(f"\nFixing {class_name}...")
        
        for file_to_fix in locations['remove_from']:
            file_path = root / file_to_fix
            if file_path.exists():
                remove_duplicate_class(file_path, class_name)
            else:
                print(f"File not found: {file_path}")
    
    print("\nDuplicate class fixes completed!")
    print("\nNote: You may need to manually adjust some imports based on the specific module structure.")

if __name__ == "__main__":
    main()