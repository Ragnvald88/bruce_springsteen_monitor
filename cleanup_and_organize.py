#!/usr/bin/env python3
"""
StealthMaster Project Cleanup and Organization Script
Cleans up the project and organizes files efficiently
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """Clean up and organize the StealthMaster project"""
    
    print("🧹 Starting StealthMaster cleanup and organization...")
    
    # Create directory structure
    dirs_to_create = [
        "archive/old_versions",
        "archive/analysis_scripts",
        "archive/test_files",
        "utilities",
        "config",
        "docs"
    ]
    
    for dir_name in dirs_to_create:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    # Define file movements
    file_movements = {
        # Old versions to archive
        "stealthmaster_backup.py": "archive/old_versions/",
        "stealthmaster_backup_20250622_202459.py": "archive/old_versions/",
        "stealthmaster_enhanced.py": "archive/old_versions/",
        "stealthmaster.py": "archive/old_versions/stealthmaster_original.py",
        "migrate_to_enhanced.py": "archive/old_versions/",
        
        # Analysis scripts to archive
        "analyze_fansale.py": "archive/analysis_scripts/",
        "analyze_fansale_advanced.py": "archive/analysis_scripts/",
        "analyze_fansale_javascript.py": "archive/analysis_scripts/",
        "capture_tickets.py": "archive/analysis_scripts/",
        
        # Test files to archive
        "test_detection.py": "archive/test_files/",
        "test_performance.py": "archive/test_files/",
        "test_stealthmaster.py": "archive/test_files/",
        "benchmark.py": "archive/test_files/",
        "debug_1_ticket_page.png": "archive/test_files/",
        "debug_2_homepage.png": "archive/test_files/",
        "fansale_raw_response.html": "archive/test_files/",
        "fansale_rendered_response.html": "archive/test_files/",
        
        # Useful utilities to keep
        "notifications.py": "utilities/",
        "captcha_solver.py": "utilities/",
        "speed_optimizations.py": "utilities/",
        "stealth_improvements.py": "utilities/",
        
        # Config files
        "config_example.yaml": "config/",
        
        # Documentation
        "performance_analysis.md": "docs/",
        "project_audit_results.json": "docs/"
    }
    
    # Move files
    print("\n📁 Moving files to organized structure...")
    for src, dst in file_movements.items():
        src_path = Path(src)
        if src_path.exists():
            dst_path = Path(dst)
            if dst.endswith('/'):
                dst_path = dst_path / src_path.name
            else:
                dst_path = Path(dst)
            
            try:
                shutil.move(str(src_path), str(dst_path))
                print(f"  ✓ Moved {src} → {dst}")
            except Exception as e:
                print(f"  ✗ Failed to move {src}: {e}")
    
    # Move old directories
    old_dirs = ["src", "utils", "test_results"]
    for old_dir in old_dirs:
        if Path(old_dir).exists():
            try:
                shutil.move(old_dir, f"archive/{old_dir}")
                print(f"  ✓ Archived directory: {old_dir}")
            except Exception as e:
                print(f"  ✗ Failed to archive {old_dir}: {e}")
    
    print("\n✅ Cleanup complete!")
    print("\n📋 New structure:")
    print("  • Main script: fansale_sniper_pro.py (your optimized version)")
    print("  • Utilities: /utilities/ (notification, captcha, optimizations)")
    print("  • Config: /config/ (example configs)")
    print("  • Archive: /archive/ (old versions and tests)")
    print("  • Logs: /logs/ (runtime logs)")
    print("  • Browser profiles: /browser_profiles/ (persistent sessions)")

if __name__ == "__main__":
    cleanup_project()
