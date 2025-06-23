#!/bin/bash
# Run StealthMaster with focus on FanSale and VivaTicket

echo "🚀 Starting StealthMaster with enhanced stealth for resale sites..."
echo ""
echo "This will:"
echo "  • Use undetected-chromedriver for better stealth"
echo "  • Apply your IPRoyal proxy automatically"
echo "  • Focus on FanSale and VivaTicket"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run with Python
python stealthmaster.py