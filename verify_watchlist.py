#!/usr/bin/env python
"""
Quick verification that watchlist system is working
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from watchlist.templates import populate_default_watchlists
from watchlist.utils import print_watchlist_summary

print("\n" + "="*70)
print("✅ WATCHLIST SYSTEM - QUICK VERIFICATION")
print("="*70)

print("\n📥 Loading pre-populated watchlists...")
watchlists = populate_default_watchlists()

print(f"✅ Created {len(watchlists)} watchlists\n")

for name, watchlist in watchlists.items():
    items = len(watchlist.get_all())
    print(f"  ✓ {name:<20} {items:>3} symbols")

print("\n" + "="*70)
print("📊 TECH MOMENTUM WATCHLIST DETAILS")
print("="*70)

tech_watchlist = watchlists["Tech Momentum"]
print_watchlist_summary(tech_watchlist)

print("\n" + "="*70)
print("🔥 QUICK ACTIONS")
print("="*70)

# Update some prices
tech_watchlist.update_price("AAPL", 155.0)
tech_watchlist.update_price("NVDA", 900.0)
tech_watchlist.update_price("TSLA", 215.0)

print("\n✓ Updated prices for: AAPL, NVDA, TSLA")

# Get alerts
from watchlist.utils import get_watchlist_alerts
alerts = get_watchlist_alerts(tech_watchlist)

print(f"\n📢 Generated {len(alerts)} alerts:")
for alert in alerts:
    print(f"   • {alert['message']}")

print("\n" + "="*70)
print("✨ WATCHLIST SYSTEM FULLY OPERATIONAL")
print("="*70)

print("""
Next Steps:
1. Review WATCHLIST_GUIDE.md for detailed documentation
2. Run: python fill_watchlist.py (for interactive demo)
3. Import watchlists into your strategies
4. Set up price monitoring and alerts
5. Export watchlists to CSV for external use

Usage Example:
  from src.watchlist.templates import populate_default_watchlists
  watchlists = populate_default_watchlists()
  tech = watchlists["Tech Momentum"]
  print(tech.get_summary())
""")

print("="*70 + "\n")
