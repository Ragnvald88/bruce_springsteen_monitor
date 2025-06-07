#!/bin/bash
# StealthMaster AI v2.0 - Quick Start Setup Script

echo "🚀 StealthMaster AI v2.0 Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo -e "${RED}Error: Run this script from your project root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Cleaning up old files...${NC}"

# Remove old files
OLD_FILES=(
    "src/core/browser_manager.py"
    "src/core/smart_browser_context_manager.py"
    "src/core/adaptive_monitor.py"
    "src/core/lightweight_monitor.py"
    "src/core/stealth_init.js"
    "src/core/stealth_integration.py"
    "src/platforms/base_monitor.py"
)

for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo -e "${RED}  ❌ Deleted: $file${NC}"
    fi
done

# Remove old directories
if [ -d "src/core/stealth" ]; then
    rm -rf "src/core/stealth"
    echo -e "${RED}  ❌ Deleted: src/core/stealth/${NC}"
fi

echo -e "\n${YELLOW}Step 2: Creating new directory structure...${NC}"

# Create new directories
mkdir -p src/stealth
mkdir -p src/platforms/adapters
mkdir -p logs
mkdir -p data/profiles
mkdir -p data/sessions
mkdir -p data/cache

echo -e "${GREEN}  ✅ Created: src/stealth/${NC}"
echo -e "${GREEN}  ✅ Created: src/platforms/adapters/${NC}"
echo -e "${GREEN}  ✅ Created: logs/${NC}"
echo -e "${GREEN}  ✅ Created: data/ structure${NC}"

# Create __init__.py files
touch src/stealth/__init__.py
touch src/platforms/adapters/__init__.py

echo -e "\n${YELLOW}Step 3: Installing/Updating dependencies...${NC}"

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install playwright>=1.40.0
pip install httpx>=0.25.0
pip install pyyaml>=6.0.1
pip install python-dotenv>=1.0.0
pip install psutil>=5.9.6
pip install numpy>=1.24.4
pip install cryptography>=41.0.7
pip install colorama>=0.4.6
pip install rich>=13.7.0

echo -e "${GREEN}  ✅ Dependencies installed${NC}"

echo -e "\n${YELLOW}Step 4: Installing Playwright browsers...${NC}"
python -m playwright install chromium
echo -e "${GREEN}  ✅ Chromium installed${NC}"

echo -e "\n${YELLOW}Step 5: Checking environment setup...${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}  ⚠️  No .env file found. Creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}  ✅ Created .env from template${NC}"
        echo -e "${YELLOW}  📝 Please edit .env and add your credentials${NC}"
    else
        echo -e "${RED}  ❌ No .env.example found${NC}"
    fi
else
    echo -e "${GREEN}  ✅ .env file exists${NC}"
fi

# Check environment variables
echo -e "\n${YELLOW}Step 6: Verifying environment variables...${NC}"

# Function to check env var
check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}  ❌ $1 is not set${NC}"
        return 1
    else
        echo -e "${GREEN}  ✅ $1 is set${NC}"
        return 0
    fi
}

# Source .env if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required variables
check_env "FANSALE_EMAIL"
check_env "FANSALE_PASSWORD"
check_env "IPROYAL_HOSTNAME"
check_env "IPROYAL_PORT"
check_env "IPROYAL_USERNAME"
check_env "IPROYAL_PASSWORD"

echo -e "\n${YELLOW}Step 7: Creating test script...${NC}"

# Create a test script
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test StealthMaster AI Setup"""

import os
import sys
from pathlib import Path

print("🔍 Testing StealthMaster AI v2.0 Setup\n")

# Check Python version
print(f"Python version: {sys.version}")
if sys.version_info < (3, 8):
    print("❌ Python 3.8+ required")
    sys.exit(1)

# Check imports
try:
    import playwright
    print("✅ Playwright installed")
except ImportError:
    print("❌ Playwright not installed")

try:
    import httpx
    print("✅ httpx installed")
except ImportError:
    print("❌ httpx not installed")

# Check environment
env_vars = ["FANSALE_EMAIL", "IPROYAL_HOSTNAME"]
for var in env_vars:
    if os.getenv(var):
        print(f"✅ {var} is set")
    else:
        print(f"❌ {var} is not set")

# Check file structure
required_files = [
    "src/main.py",
    "config/config.yaml",
]

for file in required_files:
    if Path(file).exists():
        print(f"✅ {file} exists")
    else:
        print(f"❌ {file} missing")

print("\n✨ Setup test complete!")
EOF

chmod +x test_setup.py

echo -e "${GREEN}  ✅ Created test_setup.py${NC}"

echo -e "\n${GREEN}✨ StealthMaster AI v2.0 Setup Complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Add all the new v2.0 Python files from the artifacts"
echo "2. Edit .env with your actual credentials"
echo "3. Run: python test_setup.py"
echo "4. Start hunting: python src/main.py"

echo -e "\n${GREEN}🎸 Ready to catch Bruce Springsteen tickets!${NC}"
