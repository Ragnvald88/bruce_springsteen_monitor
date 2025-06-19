#!/usr/bin/env python3
"""
Setup Script for StealthMaster V2 Upgrades
==========================================
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def run_command(cmd, description):
    """Run a command with error handling"""
    print(f"\n► {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    """Main setup process"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              STEALTHMASTER V2 UPGRADE SETUP                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Step 1: Install Docker (if not installed)
    print_header("Step 1: Checking Docker Installation")
    
    docker_installed = run_command(
        "docker --version",
        "Checking Docker"
    )
    
    if not docker_installed:
        print("\n⚠️  Docker is required for CloudFlare bypass")
        print("Please install Docker from: https://docs.docker.com/get-docker/")
        print("After installing Docker, run this script again.")
        response = input("\nContinue without Docker? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 2: Create virtual environment
    print_header("Step 2: Setting up Virtual Environment")
    
    venv_path = Path(__file__).parent.parent / "venv_v2"
    
    if not venv_path.exists():
        run_command(
            f"python -m venv {venv_path}",
            "Creating virtual environment"
        )
    
    # Activate command for different OS
    if sys.platform == "win32":
        activate_cmd = f"{venv_path}\\Scripts\\activate"
        pip_cmd = f"{venv_path}\\Scripts\\pip"
    else:
        activate_cmd = f"source {venv_path}/bin/activate"
        pip_cmd = f"{venv_path}/bin/pip"
    
    print(f"\n📌 To activate virtual environment, run:")
    print(f"   {activate_cmd}")
    
    # Step 3: Install requirements
    print_header("Step 3: Installing Requirements")
    
    requirements_file = Path(__file__).parent / "requirements_upgrade.txt"
    
    # Upgrade pip first
    run_command(
        f"{pip_cmd} install --upgrade pip",
        "Upgrading pip"
    )
    
    # Install requirements
    run_command(
        f"{pip_cmd} install -r {requirements_file}",
        "Installing requirements"
    )
    
    # Step 4: Install Playwright browsers
    print_header("Step 4: Installing Playwright Browsers")
    
    run_command(
        f"{pip_cmd} install playwright",
        "Installing Playwright"
    )
    
    run_command(
        f"{venv_path}/bin/playwright install chromium",
        "Installing Chromium for Playwright"
    )
    
    # Step 5: Pull FlareSolverr Docker image
    if docker_installed:
        print_header("Step 5: Setting up FlareSolverr")
        
        run_command(
            "docker pull ghcr.io/flaresolverr/flaresolverr:latest",
            "Pulling FlareSolverr image"
        )
    
    # Step 6: Create necessary directories
    print_header("Step 6: Creating Directories")
    
    dirs_to_create = [
        Path(__file__).parent.parent / "logs_v2",
        Path(__file__).parent.parent / "data_v2",
        Path(__file__).parent.parent / "session_data_v2"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    # Step 7: Create launcher script
    print_header("Step 7: Creating Launch Scripts")
    
    # Create run_v2.sh for Unix
    run_script_unix = Path(__file__).parent.parent / "run_v2.sh"
    with open(run_script_unix, 'w') as f:
        f.write(f"""#!/bin/bash
# StealthMaster V2 Launcher

echo "Starting StealthMaster V2..."

# Activate virtual environment
source {venv_path}/bin/activate

# Set environment variables
export PYTHONPATH="{Path(__file__).parent.parent}:$PYTHONPATH"

# Run StealthMaster V2
python {Path(__file__).parent}/stealthmaster_v2.py
""")
    
    os.chmod(run_script_unix, 0o755)
    print(f"✅ Created: {run_script_unix}")
    
    # Create run_v2.bat for Windows
    run_script_win = Path(__file__).parent.parent / "run_v2.bat"
    with open(run_script_win, 'w') as f:
        f.write(f"""@echo off
REM StealthMaster V2 Launcher

echo Starting StealthMaster V2...

REM Activate virtual environment
call {venv_path}\\Scripts\\activate

REM Set environment variables
set PYTHONPATH={Path(__file__).parent.parent};%PYTHONPATH%

REM Run StealthMaster V2
python {Path(__file__).parent}\\stealthmaster_v2.py
""")
    
    print(f"✅ Created: {run_script_win}")
    
    # Step 8: Check .env file
    print_header("Step 8: Checking Configuration")
    
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print("✅ .env file found")
        
        # Check required variables
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'FANSALE_EMAIL',
            'FANSALE_PASSWORD',
            'IPROYAL_USERNAME',
            'IPROYAL_PASSWORD',
            'TWOCAPTCHA_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("Please update your .env file with the missing variables")
    else:
        print("❌ .env file not found")
        print("Please copy .env.example to .env and update with your credentials")
    
    # Final instructions
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Ensure your .env file has all required credentials")
    print("2. Update user_info in stealthmaster_v2.py with your details")
    print("3. Run StealthMaster V2:")
    
    if sys.platform == "win32":
        print(f"   {run_script_win}")
    else:
        print(f"   ./{run_script_unix.name}")
    
    print("\n💡 Tips:")
    print("- Monitor logs in the logs_v2 directory")
    print("- FlareSolverr will start automatically")
    print("- Sessions rotate every 8 minutes")
    print("- Check proxy status in the dashboard")
    
    print("\n🎯 Good luck getting those Bruce Springsteen tickets!")

if __name__ == "__main__":
    main()
