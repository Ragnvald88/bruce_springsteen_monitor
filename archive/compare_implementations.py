#!/usr/bin/env python3
"""
Quick comparison tool for FanSale bot implementations
"""

import os
import sys

def compare_implementations():
    print("\n" + "="*70)
    print("FANSALE BOT IMPLEMENTATIONS COMPARISON")
    print("="*70 + "\n")
    
    print("📁 Available Implementations:\n")
    
    print("1. fansale_hunter_buyer.py (ACTIVE - Enhanced Hunter-Buyer)")
    print("   ✅ Each browser hunts AND buys")
    print("   ✅ Lightning-fast purchase (<1 second)")
    print("   ✅ Advanced stealth integration")
    print("   ✅ Optimized performance")
    print("   ⚡ RECOMMENDED for maximum speed\n")
    
    print("2. fansale_unified_backup.py (Previous - Unified Edition)")
    print("   ✅ Separate hunter and purchase browsers")
    print("   ✅ Queue-based ticket discovery")
    print("   ✅ More conservative approach")
    print("   ❌ Slower purchase (3-5 seconds)")
    print("   📦 Backup available if needed\n")
    
    print("="*70)
    print("To switch implementations, edit fansale.py")
    print("Current: imports from fansale_hunter_buyer")
    print("="*70 + "\n")

if __name__ == "__main__":
    compare_implementations()
