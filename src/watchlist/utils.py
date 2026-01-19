"""Watchlist utility functions and helpers"""

from typing import List, Dict
from .watchlist import Watchlist, AssetClass, WatchlistCategory


def print_watchlist_summary(watchlist: Watchlist):
    """Print watchlist summary to console"""
    summary = watchlist.get_summary()
    
    print(f"\n📊 {watchlist.name} Watchlist Summary")
    print("=" * 70)
    print(f"Total Items: {summary['total_items']}")
    
    if summary['categories']:
        print("\nBy Category:")
        for category, count in summary['categories'].items():
            print(f"  • {category:<20} {count:>3} items")
    
    if summary['asset_classes']:
        print("\nBy Asset Class:")
        for asset_class, count in summary['asset_classes'].items():
            print(f"  • {asset_class:<20} {count:>3} items")
    
    print("\nWatchlist Items:")
    print("-" * 70)
    print(f"{'Symbol':<10} {'Name':<25} {'Current':<12} {'Target':<12}")
    print("-" * 70)
    
    for item in summary['items']:
        symbol = item['symbol']
        name = item['name'][:23]
        current = f"${item['current_price']:.2f}" if item['current_price'] else "N/A"
        target = f"${item['target_price']:.2f}" if item['target_price'] else "N/A"
        print(f"{symbol:<10} {name:<25} {current:<12} {target:<12}")
    
    print("=" * 70)


def get_watchlist_alerts(watchlist: Watchlist) -> List[Dict]:
    """Get alert conditions for watchlist items"""
    alerts = []
    
    for item in watchlist.get_all():
        if item.current_price is None:
            continue
        
        # Target price reached
        if item.target_price and item.current_price >= item.target_price:
            alerts.append({
                'symbol': item.symbol,
                'type': 'TARGET_REACHED',
                'message': f"{item.symbol}: Target price ${item.target_price:.2f} reached! Current: ${item.current_price:.2f}",
                'price': item.current_price,
                'target': item.target_price
            })
        
        # Stop loss triggered
        if item.stop_loss and item.current_price <= item.stop_loss:
            alerts.append({
                'symbol': item.symbol,
                'type': 'STOP_LOSS',
                'message': f"{item.symbol}: Stop loss ${item.stop_loss:.2f} triggered! Current: ${item.current_price:.2f}",
                'price': item.current_price,
                'stop': item.stop_loss
            })
    
    return alerts


def compare_watchlists(watchlist1: Watchlist, watchlist2: Watchlist) -> Dict:
    """Compare two watchlists"""
    items1 = set(watchlist1.items.keys())
    items2 = set(watchlist2.items.keys())
    
    return {
        'only_in_first': items1 - items2,
        'only_in_second': items2 - items1,
        'in_both': items1 & items2,
        'first_count': len(watchlist1.items),
        'second_count': len(watchlist2.items),
        'overlap_pct': (len(items1 & items2) / max(len(items1), len(items2)) * 100) if max(len(items1), len(items2)) > 0 else 0
    }


def export_watchlist_to_csv(watchlist: Watchlist, filename: str):
    """Export watchlist to CSV file"""
    import csv
    
    summary = watchlist.get_summary()
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Symbol', 'Name', 'Asset Class', 'Category', 'Current Price',
            'Target Price', 'Stop Loss', 'Tags', 'Notes'
        ])
        
        for item in summary['items']:
            writer.writerow([
                item['symbol'],
                item['name'],
                item['asset_class'],
                item['category'],
                item['current_price'] or '',
                item['target_price'] or '',
                item['stop_loss'] or '',
                ','.join(item['tags']),
                ''
            ])


def import_watchlist_from_csv(filename: str, watchlist_name: str = "Imported") -> Watchlist:
    """Import watchlist from CSV file"""
    import csv
    
    watchlist = Watchlist(name=watchlist_name)
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                watchlist.add_item(
                    symbol=row['Symbol'],
                    name=row['Name'],
                    asset_class=AssetClass[row['Asset Class']],
                    category=WatchlistCategory[row['Category']],
                    target_price=float(row['Target Price']) if row['Target Price'] else None,
                    stop_loss=float(row['Stop Loss']) if row['Stop Loss'] else None,
                    tags=row['Tags'].split(',') if row['Tags'] else []
                )
            except (ValueError, KeyError) as e:
                print(f"Error importing {row.get('Symbol', 'unknown')}: {e}")
    
    return watchlist
