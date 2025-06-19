#!/bin/bash
# Quick setup for StealthMaster Resale Edition

echo "🚀 StealthMaster Resale Setup"
echo "============================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python $(python3 --version) found"

# Check/create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install minimal requirements
echo "Installing requirements..."
pip install --quiet --upgrade pip

# Core requirements only
pip install --quiet \
    playwright==1.40.0 \
    python-dotenv==1.0.0 \
    pyyaml==6.0.1 \
    aiohttp==3.9.1 \
    psutil==5.9.6 \
    rich==13.7.0

# Install Playwright browsers
echo "Installing Chrome for Playwright..."
playwright install chromium

# Make scripts executable
chmod +x stealthmaster_lite.py
chmod +x run_resale.py
chmod +x monitor_dashboard.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 How to use:"
echo "1. Run the optimized monitor:"
echo "   python stealthmaster_lite.py"
echo ""
echo "2. Or use existing system with focus on resale:"
echo "   python run_resale.py"
echo ""
echo "3. Monitor dashboard (in separate terminal):"
echo "   python monitor_dashboard.py"
echo ""
echo "⚡ Tips:"
echo "- The lite version is faster and more efficient"
echo "- Sessions rotate every 7 minutes automatically"
echo "- Fixed price tickets are purchased instantly"
echo "- You have 10 minutes to complete payment"
echo ""
echo "🎯 Target: Bruce Springsteen - Milano 2025"
echo "Good luck!"
