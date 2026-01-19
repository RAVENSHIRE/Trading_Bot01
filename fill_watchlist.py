#!/usr/bin/env python
"""
Quick watchlist filler - Populate your watchlist in seconds!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchlist.templates import populate_default_watchlists
from watchlist.utils import print_watchlist_summary, get_watchlist_alerts


def main():
    print("\n" + "="*70)
    print("🎯 TRADING BOT - WATCHLIST QUICK FILLER")
    print("="*70)
    
    print("\n📥 Creating pre-populated watchlists...")
    
    watchlists = populate_default_watchlists()
    
    for name, watchlist in watchlists.items():
        print(f"\n✓ Created: {name}")
        print(f"  📊 {len(watchlist.get_all())} stocks")
    
    print("\n" + "="*70)
    print("📊 WATCHLIST SUMMARIES")
    print("="*70)
    
    for name, watchlist in watchlists.items():
        print_watchlist_summary(watchlist)
    
    # Show alerts example
    print("\n" + "="*70)
    print("🔔 SAMPLE ALERTS (if prices were available)")
    print("="*70)
    
    tech_watchlist = watchlists["Tech Momentum"]
    
    # Simulate some price updates
    tech_watchlist.update_price("AAPL", 152.0)  # Approaching target
    tech_watchlist.update_price("NVDA", 860.0)  # Below target
    tech_watchlist.update_price("TSLA", 215.0)  # Below stop loss
    
    alerts = get_watchlist_alerts(tech_watchlist)
    
    if alerts:
        print(f"\nFound {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  • {alert['message']}")
    else:
        print("\n✓ No active alerts")
    
    print("\n" + "="*70)
    print("✅ WATCHLIST SETUP COMPLETE!")
    print("="*70)
    print("\nUsage Examples:")
    print("""
from src.watchlist.templates import populate_default_watchlists
from src.watchlist.utils import print_watchlist_summary

# Get all watchlists
watchlists = populate_default_watchlists()

# Print summary
print_watchlist_summary(watchlists["Tech Momentum"])

# Add to watchlist
watchlist = watchlists["Tech Momentum"]
watchlist.add_item(
    symbol="ADBE",
    name="Adobe Inc.",
    asset_class=AssetClass.STOCK,
    category=WatchlistCategory.GROWTH,
    target_price=580.0,
    stop_loss=480.0,
    tags=["Software", "Cloud"]
)

# Export to CSV
from src.watchlist.utils import export_watchlist_to_csv
export_watchlist_to_csv(watchlist, "my_watchlist.csv")
    """)
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
