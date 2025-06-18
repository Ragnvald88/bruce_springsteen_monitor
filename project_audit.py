#!/usr/bin/env python3
"""
StealthMaster Project Audit & Benchmarking Tool

This script performs comprehensive testing, benchmarking, and error detection
across all versions of the StealthMaster application.
"""

import os
import sys
import time
import traceback
import json
import subprocess
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import ast
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProjectAuditor:
    """Comprehensive project auditing and benchmarking."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'import_errors': [],
            'runtime_errors': [],
            'duplicate_classes': [],
            'unused_files': [],
            'benchmarks': {},
            'recommendations': []
        }
    
    def run_full_audit(self):
        """Run complete project audit."""
        logger.info("Starting StealthMaster Project Audit...")
        
        # 1. Check Python files for import errors
        self.check_import_errors()
        
        # 2. Find duplicate class definitions
        self.find_duplicate_classes()
        
        # 3. Identify unused files
        self.find_unused_files()
        
        # 4. Benchmark different versions
        self.benchmark_versions()
        
        # 5. Test basic functionality
        self.test_basic_functionality()
        
        # 6. Generate recommendations
        self.generate_recommendations()
        
        # 7. Save results
        self.save_results()
        
        logger.info("Audit complete!")
    
    def check_import_errors(self):
        """Check all Python files for import errors."""
        logger.info("Checking for import errors...")
        
        for py_file in self.root_dir.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                # Try to compile the file
                with open(py_file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
                    
                # Try to import the module (for files in src/)
                if str(py_file).startswith(str(self.root_dir / 'src')):
                    module_path = str(py_file.relative_to(self.root_dir))
                    module_name = module_path.replace('/', '.').replace('.py', '')
                    
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, py_file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    except Exception as e:
                        self.results['import_errors'].append({
                            'file': str(py_file.relative_to(self.root_dir)),
                            'error': str(e),
                            'type': 'import_error'
                        })
                        
            except SyntaxError as e:
                self.results['import_errors'].append({
                    'file': str(py_file.relative_to(self.root_dir)),
                    'error': f"Syntax error at line {e.lineno}: {e.msg}",
                    'type': 'syntax_error'
                })
            except Exception as e:
                self.results['import_errors'].append({
                    'file': str(py_file.relative_to(self.root_dir)),
                    'error': str(e),
                    'type': 'parse_error'
                })
    
    def find_duplicate_classes(self):
        """Find duplicate class definitions across the project."""
        logger.info("Finding duplicate class definitions...")
        
        class_definitions = {}
        
        for py_file in self.root_dir.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        file_path = str(py_file.relative_to(self.root_dir))
                        
                        if class_name not in class_definitions:
                            class_definitions[class_name] = []
                        class_definitions[class_name].append({
                            'file': file_path,
                            'line': node.lineno
                        })
            except:
                pass
        
        # Find duplicates
        for class_name, locations in class_definitions.items():
            if len(locations) > 1:
                self.results['duplicate_classes'].append({
                    'class': class_name,
                    'locations': locations,
                    'count': len(locations)
                })
    
    def find_unused_files(self):
        """Identify potentially unused Python files."""
        logger.info("Finding unused files...")
        
        # Get all Python files
        all_files = set()
        for py_file in self.root_dir.rglob("*.py"):
            if 'venv' not in str(py_file) and '__pycache__' not in str(py_file):
                all_files.add(str(py_file.relative_to(self.root_dir)))
        
        # Check which files are imported
        imported_files = set()
        imported_files.add('stealthmaster.py')  # Main entry points
        imported_files.add('stealthmaster_working.py')
        imported_files.add('stealthmaster_final.py')
        imported_files.add('gui_launcher.py')
        imported_files.add('test_enhancements.py')
        imported_files.add('project_audit.py')  # This file
        
        # Scan for imports
        for py_file in self.root_dir.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('src.'):
                                module_path = alias.name.replace('.', '/') + '.py'
                                imported_files.add(module_path)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('src'):
                            module_path = node.module.replace('.', '/') + '.py'
                            imported_files.add(module_path)
                            # Also add __init__.py files
                            parts = module_path.split('/')
                            for i in range(len(parts)):
                                init_path = '/'.join(parts[:i+1]) + '/__init__.py'
                                imported_files.add(init_path)
            except:
                pass
        
        # Find unused files
        unused = all_files - imported_files
        self.results['unused_files'] = sorted(list(unused))
    
    def benchmark_versions(self):
        """Benchmark different versions of the application."""
        logger.info("Benchmarking different versions...")
        
        versions = [
            ('stealthmaster.py', 'Main modular version'),
            ('stealthmaster_working.py', 'Simplified working version'),
            ('stealthmaster_final.py', 'Enhanced standalone version')
        ]
        
        for filename, description in versions:
            logger.info(f"Benchmarking {filename}...")
            
            benchmark = {
                'description': description,
                'file_size': 0,
                'line_count': 0,
                'import_time': None,
                'memory_usage': None,
                'complexity_metrics': {}
            }
            
            file_path = self.root_dir / filename
            
            # File metrics
            if file_path.exists():
                benchmark['file_size'] = file_path.stat().st_size
                with open(file_path, 'r', encoding='utf-8') as f:
                    benchmark['line_count'] = len(f.readlines())
                
                # Import time test
                start_time = time.time()
                try:
                    if filename == 'stealthmaster.py':
                        # Test if imports work
                        result = subprocess.run(
                            [sys.executable, '-c', 'import stealthmaster'],
                            capture_output=True,
                            text=True,
                            cwd=str(self.root_dir)
                        )
                        if result.returncode == 0:
                            benchmark['import_time'] = time.time() - start_time
                    else:
                        # Just parse the file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ast.parse(f.read())
                        benchmark['import_time'] = time.time() - start_time
                except Exception as e:
                    benchmark['import_error'] = str(e)
                
                # Count classes, functions, imports
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        
                    benchmark['complexity_metrics'] = {
                        'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                        'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                        'imports': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
                    }
                except:
                    pass
            
            self.results['benchmarks'][filename] = benchmark
    
    def test_basic_functionality(self):
        """Test basic functionality of each version."""
        logger.info("Testing basic functionality...")
        
        # Test if config.yaml exists
        config_path = self.root_dir / 'config.yaml'
        if not config_path.exists():
            self.results['runtime_errors'].append({
                'component': 'config.yaml',
                'error': 'Configuration file missing',
                'severity': 'high'
            })
        
        # Test if required directories exist
        required_dirs = ['data', 'logs', 'src']
        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                self.results['runtime_errors'].append({
                    'component': dir_name,
                    'error': f'Required directory {dir_name} missing',
                    'severity': 'medium'
                })
        
        # Check for required dependencies
        try:
            import selenium
            import rich
            import playwright
            import yaml
        except ImportError as e:
            self.results['runtime_errors'].append({
                'component': 'dependencies',
                'error': f'Missing dependency: {str(e)}',
                'severity': 'high'
            })
    
    def generate_recommendations(self):
        """Generate recommendations based on audit results."""
        logger.info("Generating recommendations...")
        
        # Recommendation: Clean up duplicate files
        if len(self.results['duplicate_classes']) > 0:
            self.results['recommendations'].append({
                'priority': 'HIGH',
                'category': 'Code Quality',
                'issue': f"Found {len(self.results['duplicate_classes'])} duplicate class definitions",
                'action': 'Remove duplicate class definitions, especially PatternAnalyzer in interceptor.py'
            })
        
        # Recommendation: Remove unused versions
        self.results['recommendations'].append({
            'priority': 'HIGH',
            'category': 'Project Structure',
            'issue': 'Multiple versions of main script exist',
            'action': 'Keep only stealthmaster.py as the main version, move others to examples/ or archive/'
        })
        
        # Recommendation: Clean up unused files
        if len(self.results['unused_files']) > 10:
            self.results['recommendations'].append({
                'priority': 'MEDIUM',
                'category': 'Project Structure',
                'issue': f"Found {len(self.results['unused_files'])} potentially unused files",
                'action': 'Review and remove unused files from src/ directory'
            })
        
        # Recommendation: Fix import errors
        if len(self.results['import_errors']) > 0:
            self.results['recommendations'].append({
                'priority': 'HIGH',
                'category': 'Code Quality',
                'issue': f"Found {len(self.results['import_errors'])} files with import errors",
                'action': 'Fix import errors to ensure all modules are properly loadable'
            })
        
        # Recommendation: Consolidate documentation
        self.results['recommendations'].append({
            'priority': 'MEDIUM',
            'category': 'Documentation',
            'issue': 'Multiple overlapping documentation files',
            'action': 'Consolidate documentation into README.md and a single ARCHITECTURE.md'
        })
    
    def save_results(self):
        """Save audit results to file."""
        output_file = self.root_dir / 'project_audit_results.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        # Also create a summary report
        self.create_summary_report()
    
    def create_summary_report(self):
        """Create a human-readable summary report."""
        report_file = self.root_dir / 'PROJECT_AUDIT_REPORT.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# StealthMaster Project Audit Report\n\n")
            f.write(f"Generated: {self.results['timestamp']}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- Import Errors: {len(self.results['import_errors'])}\n")
            f.write(f"- Runtime Errors: {len(self.results['runtime_errors'])}\n")
            f.write(f"- Duplicate Classes: {len(self.results['duplicate_classes'])}\n")
            f.write(f"- Unused Files: {len(self.results['unused_files'])}\n\n")
            
            f.write("## Critical Issues\n\n")
            
            # Duplicate classes
            if self.results['duplicate_classes']:
                f.write("### Duplicate Class Definitions\n\n")
                for dup in self.results['duplicate_classes']:
                    f.write(f"- **{dup['class']}** ({dup['count']} occurrences)\n")
                    for loc in dup['locations']:
                        f.write(f"  - {loc['file']}:{loc['line']}\n")
                f.write("\n")
            
            # Import errors
            if self.results['import_errors']:
                f.write("### Import Errors\n\n")
                for error in self.results['import_errors'][:10]:  # Show first 10
                    f.write(f"- {error['file']}: {error['error']}\n")
                if len(self.results['import_errors']) > 10:
                    f.write(f"- ... and {len(self.results['import_errors']) - 10} more\n")
                f.write("\n")
            
            f.write("## Version Comparison\n\n")
            f.write("| Version | Lines | Size (KB) | Classes | Functions | Description |\n")
            f.write("|---------|-------|-----------|---------|-----------|-------------|\n")
            
            for filename, data in self.results['benchmarks'].items():
                f.write(f"| {filename} | {data['line_count']} | ")
                f.write(f"{data['file_size']//1024} | ")
                f.write(f"{data['complexity_metrics'].get('classes', 'N/A')} | ")
                f.write(f"{data['complexity_metrics'].get('functions', 'N/A')} | ")
                f.write(f"{data['description']} |\n")
            
            f.write("\n## Recommendations\n\n")
            for rec in sorted(self.results['recommendations'], key=lambda x: x['priority']):
                f.write(f"### {rec['priority']} - {rec['category']}\n")
                f.write(f"**Issue:** {rec['issue']}\n")
                f.write(f"**Action:** {rec['action']}\n\n")
            
            f.write("\n## Next Steps\n\n")
            f.write("1. Fix duplicate PatternAnalyzer class in src/network/interceptor.py\n")
            f.write("2. Archive stealthmaster_working.py and stealthmaster_final.py\n")
            f.write("3. Remove unused files from src/ directory\n")
            f.write("4. Consolidate documentation files\n")
            f.write("5. Fix import errors in modules\n")
            f.write("6. Run tests to ensure functionality\n")
        
        logger.info(f"Summary report saved to {report_file}")


if __name__ == "__main__":
    auditor = ProjectAuditor()
    auditor.run_full_audit()