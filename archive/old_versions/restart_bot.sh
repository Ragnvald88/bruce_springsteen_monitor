#!/bin/bash
# Restart bot with fixes

echo "🛑 Stopping existing processes..."
pkill -f "Google Chrome" 2>/dev/null
pkill -f "chromedriver" 2>/dev/null
pkill -f "python.*fansale" 2>/dev/null

echo "⏳ Waiting for cleanup..."
sleep 3

echo "✅ Starting bot with fixes..."
echo -e "2\n2\n6\n\n" | python3 fansale_check.py