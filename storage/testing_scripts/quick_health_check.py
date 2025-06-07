#!/usr/bin/env python3
"""
Quick health check for the Bruce Springsteen ticket monitoring system
Identifies common issues and configuration problems
"""

import os
import sys
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

class QuickHealthCheck:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.checks_passed = []
    
    def check_config_file(self) -> bool:
        """Check if config file exists and is valid"""
        config_path = Path("config/config.yaml")
        
        if not config_path.exists():
            self.issues.append("❌ Config file not found at config/config.yaml")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check essential sections
            required_sections = ['targets', 'monitoring_settings', 'profile_manager', 'network']
            missing_sections = [s for s in required_sections if s not in config]
            
            if missing_sections:
                self.issues.append(f"❌ Missing config sections: {', '.join(missing_sections)}")
                return False
            
            # Check targets
            targets = config.get('targets', [])
            enabled_targets = [t for t in targets if t.get('enabled', False)]
            
            if not enabled_targets:
                self.warnings.append("⚠️ No enabled targets in configuration")
            else:
                self.checks_passed.append(f"✅ Config file valid with {len(enabled_targets)} enabled targets")
            
            # Check for environment variables in config
            config_str = str(config)
            if '${' in config_str:
                env_vars = []
                import re
                for match in re.finditer(r'\$\{([^}]+)\}', config_str):
                    env_var = match.group(1)
                    if not os.getenv(env_var):
                        env_vars.append(env_var)
                
                if env_vars:
                    self.warnings.append(f"⚠️ Missing environment variables: {', '.join(env_vars)}")
            
            return True
            
        except Exception as e:
            self.issues.append(f"❌ Config file parse error: {str(e)}")
            return False
    
    def check_required_modules(self) -> bool:
        """Check if all required Python modules can be imported"""
        required_modules = [
            ('playwright', 'playwright'),
            ('httpx', 'httpx'),
            ('yaml', 'pyyaml'),
            ('numpy', 'numpy'),
            ('psutil', 'psutil')
        ]
        
        missing_modules = []
        
        for module_name, package_name in required_modules:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                missing_modules.append(package_name)
        
        if missing_modules:
            self.issues.append(f"❌ Missing Python packages: {', '.join(missing_modules)}")
            self.issues.append("   Run: pip install -r requirements.txt")
            return False
        
        self.checks_passed.append("✅ All required Python packages installed")
        return True
    
    def check_file_structure(self) -> bool:
        """Check if essential files and directories exist"""
        essential_paths = [
            ('src/__init__.py', 'file'),
            ('src/main.py', 'file'),
            ('src/core/orchestrator.py', 'file'),
            ('src/core/components.py', 'file'),
            ('src/profiles/manager.py', 'file'),
            ('src/platforms/fansale.py', 'file'),
            ('logs', 'dir'),
            ('storage', 'dir')
        ]
        
        missing_paths = []
        
        for path_str, path_type in essential_paths:
            path = Path(path_str)
            if path_type == 'file' and not path.is_file():
                missing_paths.append(f"{path_str} (file)")
            elif path_type == 'dir' and not path.is_dir():
                missing_paths.append(f"{path_str} (directory)")
        
        if missing_paths:
            self.issues.append(f"❌ Missing essential paths: {', '.join(missing_paths)}")
            return False
        
        self.checks_passed.append("✅ Essential file structure intact")
        return True
    
    def check_stealth_components(self) -> bool:
        """Check if stealth components are properly set up"""
        stealth_paths = [
            'src/core/stealth/stealth_engine.py',
            'src/core/stealth/stealth_integration.py',
            'src/core/stealth/ultra_stealth.py'
        ]
        
        missing_stealth = []
        
        for path_str in stealth_paths:
            if not Path(path_str).exists():
                missing_stealth.append(path_str)
        
        if missing_stealth:
            self.warnings.append(f"⚠️ Missing stealth components: {', '.join(missing_stealth)}")
            self.warnings.append("   System may have reduced anti-detection capabilities")
            return False
        
        self.checks_passed.append("✅ Stealth components present")
        return True
    
    def check_permissions(self) -> bool:
        """Check file permissions"""
        executable_files = ['src/main.py']
        writable_dirs = ['logs', 'storage', 'session_backups']
        
        permission_issues = []
        
        # Check executable permissions
        for file_path in executable_files:
            path = Path(file_path)
            if path.exists() and not os.access(path, os.X_OK):
                permission_issues.append(f"{file_path} (not executable)")
        
        # Check writable directories
        for dir_path in writable_dirs:
            path = Path(dir_path)
            if path.exists() and not os.access(path, os.W_OK):
                permission_issues.append(f"{dir_path} (not writable)")
            elif not path.exists():
                # Try to create it
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception:
                    permission_issues.append(f"{dir_path} (cannot create)")
        
        if permission_issues:
            self.warnings.append(f"⚠️ Permission issues: {', '.join(permission_issues)}")
            return False
        
        self.checks_passed.append("✅ File permissions correct")
        return True
    
    def generate_report(self):
        """Generate health check report"""
        print("\n" + "="*80)
        print("🏥 BRUCE SPRINGSTEEN TICKET MONITOR - HEALTH CHECK")
        print("="*80)
        
        # Run all checks
        checks = [
            ("Configuration File", self.check_config_file),
            ("Required Modules", self.check_required_modules),
            ("File Structure", self.check_file_structure),
            ("Stealth Components", self.check_stealth_components),
            ("File Permissions", self.check_permissions)
        ]
        
        total_checks = len(checks)
        passed_checks = 0
        
        print("\n📋 Running health checks...\n")
        
        for check_name, check_func in checks:
            print(f"Checking {check_name}...", end=" ")
            try:
                result = check_func()
                if result:
                    print("✅")
                    passed_checks += 1
                else:
                    print("❌")
            except Exception as e:
                print(f"❌ Error: {e}")
                self.issues.append(f"❌ {check_name} check failed: {str(e)}")
        
        # Summary
        print("\n" + "-"*80)
        print(f"\n📊 Summary: {passed_checks}/{total_checks} checks passed")
        
        # Report issues
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
        
        # Report warnings
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Report successes
        if self.checks_passed:
            print(f"\n✅ PASSED CHECKS ({len(self.checks_passed)}):")
            for check in self.checks_passed:
                print(f"   {check}")
        
        # Overall status
        print("\n" + "-"*80)
        if self.issues:
            print("\n🚦 STATUS: ❌ NOT READY TO RUN")
            print("   Fix critical issues before running the system")
        elif self.warnings:
            print("\n🚦 STATUS: ⚠️ READY WITH WARNINGS")
            print("   System can run but may have limited functionality")
        else:
            print("\n🚦 STATUS: ✅ READY TO RUN")
            print("   All health checks passed!")
        
        # Quick start instructions
        if not self.issues:
            print("\n📌 To run the system:")
            print("   1. Ensure environment variables are set (if using proxy/auth)")
            print("   2. Run: python src/main.py")
            print("   3. Or run comprehensive tests: python run_all_tests.py")

def main():
    """Run quick health check"""
    checker = QuickHealthCheck()
    checker.generate_report()

if __name__ == "__main__":
    main()