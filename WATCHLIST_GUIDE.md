# 📊 Watchlist System Documentation

## Overview

The **Watchlist System** is a comprehensive stock/asset tracking module that allows you to:
- ✅ Create and manage multiple watchlists
- ✅ Track 40+ pre-populated stocks across 5 themes
- ✅ Set target prices and stop losses
- ✅ Filter by category, asset class, or tags
- ✅ Export/import watchlists to CSV
- ✅ Generate price alerts
- ✅ Persistent SQLite storage

---

## Quick Start

### 1. Load Pre-populated Watchlists

```python
from src.watchlist.templates import populate_default_watchlists
from src.watchlist.utils import print_watchlist_summary

# Create all default watchlists
watchlists = populate_default_watchlists()

# Print summary of Tech Momentum watchlist
print_watchlist_summary(watchlists["Tech Momentum"])
```

### 2. Add Your Own Items

```python
from src.watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory

watchlist = watchlists["Tech Momentum"]

# Add a stock
watchlist.add_item(
    symbol="ADBE",
    name="Adobe Inc.",
    asset_class=AssetClass.STOCK,
    category=WatchlistCategory.GROWTH,
    target_price=580.0,
    stop_loss=480.0,
    notes="Creative cloud platform",
    tags=["Software", "Cloud", "Design"]
)
```

### 3. Query Your Watchlist

```python
# Get all items
all_items = watchlist.get_all()

# Get by category
momentum_items = watchlist.get_by_category(WatchlistCategory.MOMENTUM)

# Get by asset class
stocks = watchlist.get_by_asset_class(AssetClass.STOCK)

# Get by tag
cloud_stocks = watchlist.get_by_tag("Cloud")

# Get specific item
apple = watchlist.get_item("AAPL")
```

---

## Pre-populated Watchlists

### 1. 📱 Tech Momentum (8 stocks)
Focus on technology companies with strong momentum and growth

**Stocks:** AAPL, MSFT, NVDA, GOOGL, META, TSLA, AMD, AVGO

```python
watchlist = watchlists["Tech Momentum"]
watchlist.get_summary()
```

### 2. 💰 Dividend Growth (8 stocks)
Stable dividend-paying companies with income focus

**Stocks:** JNJ, PG, KO, MCD, PEP, CSCO, INTC, VZ

```python
watchlist = watchlists["Dividend Growth"]
```

### 3. 💎 Value Picks (8 stocks)
Undervalued companies with recovery potential

**Stocks:** JPM, BAC, F, GE, XOM, CVX, BTU, IBM

```python
watchlist = watchlists["Value Picks"]
```

### 4. 🚀 Growth Stories (8 stocks)
High-growth companies in cloud, SaaS, and technology

**Stocks:** ASML, AXON, CRM, NOW, ADBE, OKTA, PAYC, APP

```python
watchlist = watchlists["Growth Stories"]
```

### 5. 🏦 ETF Portfolio (8 ETFs)
Broad market exposure and diversification

**ETFs:** SPY, QQQ, IWM, VTI, AGG, GLD, TLT, VGK

```python
watchlist = watchlists["ETF Portfolio"]
```

---

## Core Classes

### `Watchlist`
Main watchlist container

```python
from src.watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory

# Create watchlist
watchlist = Watchlist(name="My Watchlist")

# Add items
watchlist.add_item(
    symbol="AAPL",
    name="Apple Inc.",
    asset_class=AssetClass.STOCK,
    category=WatchlistCategory.MOMENTUM,
    target_price=160.0,
    stop_loss=140.0,
    notes="Strong momentum",
    tags=["Tech", "Large-Cap"]
)

# Update prices
watchlist.update_price("AAPL", 155.0)

# Query
apple = watchlist.get_item("AAPL")

# Remove
watchlist.remove_item("AAPL")

# Get summary
summary = watchlist.get_summary()
```

### `MultiWatchlist`
Manage multiple watchlists

```python
from src.watchlist.watchlist import MultiWatchlist

multi = MultiWatchlist()

# Create watchlist
tech_list = multi.create_watchlist("Tech", "Technology stocks")

# Get watchlist
tech_list = multi.get_watchlist("Tech")

# List all
all_names = multi.list_watchlists()
```

### `WatchlistItem`
Individual item in watchlist

```python
@dataclass
class WatchlistItem:
    symbol: str                          # Stock ticker
    name: str                            # Company name
    asset_class: AssetClass              # STOCK, ETF, CRYPTO, etc.
    category: WatchlistCategory          # MOMENTUM, VALUE, GROWTH, etc.
    added_date: datetime                 # When added
    current_price: Optional[float] = None        # Current market price
    target_price: Optional[float] = None         # Target price for exit
    stop_loss: Optional[float] = None           # Stop loss level
    notes: str = ""                             # Custom notes
    tags: List[str] = None                      # Tags for filtering
```

---

## Enumerations

### `AssetClass`
```python
STOCK      # Stock
ETF        # Exchange Traded Fund
CRYPTO     # Cryptocurrency
FOREX      # Foreign Exchange
FUTURES    # Futures Contracts
OPTION     # Options
```

### `WatchlistCategory`
```python
MOMENTUM    # Momentum/technical plays
VALUE       # Value investing
GROWTH      # High-growth companies
DIVIDEND    # Dividend/income stocks
TECHNICAL   # Technical analysis focus
FUNDAMENTAL # Fundamental analysis focus
CUSTOM      # Custom category
```

---

## Utility Functions

### Print Summary

```python
from src.watchlist.utils import print_watchlist_summary

watchlist = watchlists["Tech Momentum"]
print_watchlist_summary(watchlist)

# Output:
# 📊 Tech Momentum Watchlist Summary
# =======================================
# Total Items: 8
# By Category: MOMENTUM: 8
# By Asset Class: STOCK: 8
# 
# Watchlist Items:
# Symbol     Name                    Current     Target
# AAPL       Apple Inc.              N/A         N/A
# ...
```

### Get Alerts

```python
from src.watchlist.utils import get_watchlist_alerts

# Update prices
watchlist.update_price("AAPL", 160.5)
watchlist.update_price("TSLA", 215.0)

# Get alerts
alerts = get_watchlist_alerts(watchlist)

# Output:
# [
#   {
#     'symbol': 'AAPL',
#     'type': 'TARGET_REACHED',
#     'message': 'AAPL: Target price $160.00 reached!',
#     'price': 160.5,
#     'target': 160.0
#   },
#   {
#     'symbol': 'TSLA',
#     'type': 'STOP_LOSS',
#     'message': 'TSLA: Stop loss $220.00 triggered!',
#     'price': 215.0,
#     'stop': 220.0
#   }
# ]
```

### Compare Watchlists

```python
from src.watchlist.utils import compare_watchlists

comparison = compare_watchlists(
    watchlists["Tech Momentum"],
    watchlists["Growth Stories"]
)

# Output:
# {
#   'only_in_first': {'TSLA', 'MSFT', ...},
#   'only_in_second': {'ASML', 'CRM', ...},
#   'in_both': {'ADBE', 'NVDA'},
#   'first_count': 8,
#   'second_count': 8,
#   'overlap_pct': 25.0
# }
```

### Export to CSV

```python
from src.watchlist.utils import export_watchlist_to_csv

watchlist = watchlists["Tech Momentum"]
export_watchlist_to_csv(watchlist, "tech_watchlist.csv")
```

### Import from CSV

```python
from src.watchlist.utils import import_watchlist_from_csv

watchlist = import_watchlist_from_csv(
    "my_watchlist.csv",
    watchlist_name="Imported List"
)
```

---

## Tag Management

### Add Tags

```python
watchlist.add_tag("AAPL", "Large-Cap")
watchlist.add_tag("AAPL", "Blue-Chip")

# Get item
item = watchlist.get_item("AAPL")
print(item.tags)  # ['Large-Cap', 'Blue-Chip']
```

### Filter by Tag

```python
large_caps = watchlist.get_by_tag("Large-Cap")

for item in large_caps:
    print(f"{item.symbol}: {item.name}")
```

### Remove Tags

```python
watchlist.remove_tag("AAPL", "Large-Cap")
```

---

## Quick Fill Script

Run the quick fill script to populate all watchlists:

```bash
python fill_watchlist.py
```

Output:
```
🎯 TRADING BOT - WATCHLIST QUICK FILLER
=======================================================
📥 Creating pre-populated watchlists...

✓ Created: Tech Momentum
  📊 8 stocks
✓ Created: Dividend Growth
  📊 8 stocks
✓ Created: Value Picks
  📊 8 stocks
✓ Created: Growth Stories
  📊 8 stocks
✓ Created: ETF Portfolio
  📊 8 stocks

📊 WATCHLIST SUMMARIES
=======================================================
...

✅ WATCHLIST SETUP COMPLETE!
```

---

## Integration with Portfolio

```python
from src.core.portfolio import Portfolio
from src.watchlist.templates import populate_default_watchlists

# Create portfolio
portfolio = Portfolio(initial_capital=100000)

# Load watchlists
watchlists = populate_default_watchlists()

# Get tech stocks for trading
tech_watchlist = watchlists["Tech Momentum"]

# Check which stocks are in watchlist
for item in tech_watchlist.get_all():
    print(f"{item.symbol}: {item.name}")
    print(f"  Target: ${item.target_price}")
    print(f"  Stop Loss: ${item.stop_loss}")
```

---

## Database

Watchlists are stored in SQLite for persistence:

```
data/watchlist.db
├── watchlist table
│   ├── symbol (PRIMARY KEY)
│   ├── name
│   ├── asset_class
│   ├── category
│   ├── added_date
│   ├── current_price
│   ├── target_price
│   ├── stop_loss
│   ├── notes
│   └── tags
│
└── Indexes
    ├── idx_category
    └── idx_asset_class
```

---

## Testing

Run watchlist tests:

```bash
python -m pytest tests/test_watchlist.py -v
```

Tests include:
- ✓ Watchlist creation
- ✓ Add/remove items
- ✓ Update prices
- ✓ Filter by category
- ✓ Filter by asset class
- ✓ Tag functionality
- ✓ Persistence

---

## Best Practices

### 1. Organize by Categories
```python
# Good: Clear categorization
watchlist.add_item(..., category=WatchlistCategory.MOMENTUM)

# Better: Add tags too
watchlist.add_item(..., tags=["Tech", "High-Growth"])
```

### 2. Set Targets and Stops
```python
# Always set exit points
watchlist.add_item(
    symbol="AAPL",
    target_price=160.0,  # Take profit at
    stop_loss=140.0      # Cut loss at
)
```

### 3. Use Tags for Filtering
```python
# Create meaningful tags
watchlist.add_item(..., tags=["Tech", "Large-Cap", "Dividend"])

# Query easily
tech_stocks = watchlist.get_by_tag("Tech")
```

### 4. Regular Updates
```python
# Update prices daily
watchlist.update_price("AAPL", 155.50)

# Check for alerts
alerts = get_watchlist_alerts(watchlist)
```

---

## Examples

### Build Custom Watchlist

```python
from src.watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory

# Create watchlist
my_list = Watchlist(name="My Strategy")

# Add carefully selected stocks
stocks = [
    ("AAPL", "Apple", 160.0, 140.0),
    ("MSFT", "Microsoft", 400.0, 360.0),
    ("GOOGL", "Google", 155.0, 130.0),
]

for symbol, name, target, stop in stocks:
    my_list.add_item(
        symbol=symbol,
        name=name,
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM,
        target_price=target,
        stop_loss=stop,
        tags=["Tech", "Quality"]
    )

# Export
export_watchlist_to_csv(my_list, "my_strategy.csv")
```

---

## Summary

| Feature | Capability |
|---------|-----------|
| Pre-populated | ✅ 5 watchlists, 40+ stocks |
| Create Custom | ✅ Unlimited watchlists |
| Persistence | ✅ SQLite database |
| Filtering | ✅ By category, asset, tags |
| Price Tracking | ✅ Current, target, stop |
| Alerts | ✅ Target reached, stop triggered |
| Export/Import | ✅ CSV support |
| Tags | ✅ Custom tagging system |
| Integration | ✅ Works with portfolio/signals |

Your watchlist system is ready! 🚀
