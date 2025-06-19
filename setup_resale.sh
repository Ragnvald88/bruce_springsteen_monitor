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

# Install requirements
echo "Installing requirements..."
pip install --quiet --upgrade pip

# Install from requirements.txt
pip install --quiet -r requirements.txt

# Make scripts executable
chmod +x run_resale.py
chmod +x run_stealth.sh
chmod +x monitor_dashboard.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 How to use:"
echo "1. Run the resale-focused monitor:"
echo "   python run_resale.py"
echo ""
echo "2. Or use the shell script:"
echo "   ./run_stealth.sh"
echo ""
echo "3. Monitor dashboard (in separate terminal):"
echo "   python monitor_dashboard.py"
echo ""
echo "⚡ Features:"
echo "- Uses undetected-chromedriver for better stealth"
echo "- Automatic proxy configuration"
echo "- Fixed price tickets are purchased instantly"
echo "- You have 10 minutes to complete payment"
echo ""
echo "🎯 Target: Bruce Springsteen - Milano 2025"
echo "Good luck!"