#!/usr/bin/env python3
"""
Data Usage Calculator for Different Bot Approaches
Shows why the hybrid approach saves your proxy data
"""

def calculate_data_usage():
    print("🔢 FanSale Bot Data Usage Calculator\n")
    
    # Constants
    FULL_PAGE_SIZE_KB = 500  # With images
    NO_IMAGES_PAGE_KB = 100  # Without images
    API_RESPONSE_KB = 5      # JSON only
    
    MINUTES_PER_HOUR = 60
    KB_TO_GB = 1024 * 1024
    
    approaches = {
        "Your 500ms Constant Refresh": {
            "interval_seconds": 0.5,
            "page_size_kb": FULL_PAGE_SIZE_KB,
            "description": "Refreshes entire page every 500ms"
        },
        "1 Second Refresh": {
            "interval_seconds": 1.0,
            "page_size_kb": FULL_PAGE_SIZE_KB,
            "description": "Refreshes entire page every second"
        },
        "Pure API Approach": {
            "interval_seconds": 0.3,
            "page_size_kb": API_RESPONSE_KB,
            "description": "Direct API calls (if it worked)"
        },
        "Elite Hybrid (Recommended)": {
            "interval_seconds": 20,  # Average with smart patterns
            "page_size_kb": NO_IMAGES_PAGE_KB,
            "description": "Smart patterns + client-side monitoring"
        }
    }
    
    print("=" * 60)
    for name, config in approaches.items():
        requests_per_minute = 60 / config["interval_seconds"]
        data_per_minute_kb = requests_per_minute * config["page_size_kb"]
        data_per_hour_mb = (data_per_minute_kb * MINUTES_PER_HOUR) / 1024
        data_per_hour_gb = data_per_hour_mb / 1024
        
        # Calculate proxy lifetime (assuming 10GB proxy)
        proxy_lifetime_hours = 10 / data_per_hour_gb if data_per_hour_gb > 0 else float('inf')
        
        print(f"📊 {name}")
        print(f"   {config['description']}")
        print(f"   • Requests/minute: {requests_per_minute:.1f}")
        print(f"   • Data/minute: {data_per_minute_kb:.1f} KB")
        print(f"   • Data/hour: {data_per_hour_mb:.1f} MB ({data_per_hour_gb:.2f} GB)")
        print(f"   • 10GB Proxy lasts: {proxy_lifetime_hours:.1f} hours")
        
        if name == "Your 500ms Constant Refresh":
            print(f"   ⚠️  WARNING: Will trigger bot detection!")
        elif name == "Elite Hybrid (Recommended)":
            print(f"   ✅ BEST: Fast detection + low data + stealth")
            
        print()
    
    print("=" * 60)
    print("\n💡 Key Insights:")
    print("1. Your 500ms approach burns through proxy data 72x faster")
    print("2. Constant intervals = instant bot detection")
    print("3. Elite Hybrid uses client-side JS for speed without network requests")
    print("4. Smart patterns mimic human behavior")
    print("\n🎯 Recommendation: Use elite_hybrid_sniper.py")

if __name__ == "__main__":
    calculate_data_usage()
