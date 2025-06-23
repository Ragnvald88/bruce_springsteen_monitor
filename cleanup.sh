#!/bin/bash
# Cleanup script for StealthMaster project

echo "🧹 StealthMaster Cleanup Script"
echo "================================"
echo ""
echo "This will remove redundant files and organize your project."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Create backup first
echo "📦 Creating backup..."
mkdir -p backups
cp -r archive backups/archive_$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Remove redundant files
echo "🗑️  Removing redundant files..."

# Remove archive folder
rm -rf archive

# Remove old backups
rm -f fansale_original_backup.py
rm -f fansale_v2.py

# Remove old markdown files (keep README and PROJECT_ANALYSIS)
rm -f ENHANCEMENT_SUMMARY.md
rm -f FILTER_EXAMPLES.md
rm -f FIXES_GUIDE.md
rm -f INTEGRATION_ANALYSIS.md
rm -f QUICK_GIT_FIX.md
rm -f SIMPLIFICATION_SUMMARY.md

# Remove old screenshots (keep recent ones)
find . -name "*.png" -mtime +7 -delete 2>/dev/null

# Clean pycache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining structure:"
ls -la

echo ""
echo "🚀 To run the bot:"
echo "   Original (fixed): python fansale.py"
echo "   Optimized:        python fansale_stealth.py"
