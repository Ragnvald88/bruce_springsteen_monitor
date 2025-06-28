#!/bin/bash
# Run the FanSale bot with proper configuration

echo "🎫 Starting FanSale Bot v7..."
echo ""
echo "Chrome Version: 137 (detected)"
echo ""

# Default configuration for testing
cat > .env.test << EOF
FANSALE_TARGET_URL=https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388
TWOCAPTCHA_API_KEY=c58050aca5076a2a26ba2eff1c429d4d
EOF

# Create default input for automated testing
cat > bot_input.txt << EOF
2
2
6
EOF

echo "Running with default configuration:"
echo "- 2 browsers"
echo "- Max 2 tickets"
echo "- All ticket types"
echo ""

# Run the bot with input
python3 fansale_check.py < bot_input.txt

# Clean up
rm -f bot_input.txt .env.test