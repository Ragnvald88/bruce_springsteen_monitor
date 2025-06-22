#!/bin/bash
# Fix dependencies for Python 3.13

echo "🔧 Fixing StealthMaster dependencies for Python 3.13..."
echo "=================================================="

cd /Users/macbookpro_ronald/Documents/Personal/Projects/stealthmaster

# Upgrade pip first
echo "📦 Upgrading pip..."
./venv/bin/python -m pip install --upgrade pip

# Install setuptools with distutils compatibility
echo "📦 Installing setuptools..."
./venv/bin/pip install --upgrade setuptools wheel

# For Python 3.13, we need to install the compatibility package
echo "📦 Installing Python 3.13 compatibility packages..."
./venv/bin/pip install --upgrade setuptools-distutils-reinstall

# Uninstall old undetected-chromedriver
echo "🗑️ Removing old undetected-chromedriver..."
./venv/bin/pip uninstall -y undetected-chromedriver

# Install the latest version that supports Python 3.13
echo "📦 Installing latest undetected-chromedriver..."
./venv/bin/pip install undetected-chromedriver>=3.6.0

# Ensure selenium-wire is installed
echo "📦 Installing selenium-wire..."
./venv/bin/pip install selenium-wire

# Install other required packages
echo "📦 Installing other dependencies..."
./venv/bin/pip install python-dotenv PyYAML requests colorlog

echo ""
echo "✅ Dependencies fixed! Testing import..."
./venv/bin/python -c "import undetected_chromedriver as uc; print('✅ undetected_chromedriver imported successfully!')"

echo ""
echo "🎯 Ready to run: ./venv/bin/python fansale_final.py"
