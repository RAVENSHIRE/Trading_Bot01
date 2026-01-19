"""Watchlist management system"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3
from pathlib import Path


class AssetClass(Enum):
    """Asset class types"""
    STOCK = "STOCK"
    ETF = "ETF"
    BOND = "BOND"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    FUTURES = "FUTURES"
    OPTION = "OPTION"


class WatchlistCategory(Enum):
    """Watchlist categories"""
    MOMENTUM = "MOMENTUM"
    VALUE = "VALUE"
    GROWTH = "GROWTH"
    DIVIDEND = "DIVIDEND"
    INCOME = "INCOME"
    TECHNICAL = "TECHNICAL"
    FUNDAMENTAL = "FUNDAMENTAL"
    CUSTOM = "CUSTOM"


@dataclass
class WatchlistItem:
    """Individual watchlist item"""
    symbol: str
    name: str
    asset_class: AssetClass
    category: WatchlistCategory
    added_date: Optional[datetime] = None
    current_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    notes: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.added_date is None:
            self.added_date = datetime.now()


class Watchlist:
    """Main watchlist manager"""
    
    def __init__(self, name: str = "Default", db_path: str = "data/watchlist.db"):
        self.name = name
        self.db_path = db_path
        self.items: Dict[str, WatchlistItem] = {}
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._load_from_db()
    
    def _init_db(self):
        """Initialize watchlist database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    asset_class TEXT,
                    category TEXT,
                    added_date TEXT,
                    current_price REAL,
                    target_price REAL,
                    stop_loss REAL,
                    notes TEXT,
                    tags TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON watchlist(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_class ON watchlist(asset_class)")
    
    def add_item(self, symbol_or_item=None, name: str = None, asset_class: AssetClass = None,
                 category: WatchlistCategory = None, target_price: Optional[float] = None,
                 stop_loss: Optional[float] = None, notes: str = "", 
                 tags: Optional[List[str]] = None, symbol: str = None) -> WatchlistItem:
        """Add item to watchlist
        
        Can be called in three ways:
        1. add_item(WatchlistItem(...)) - pass a WatchlistItem object
        2. add_item('AAPL', name='Apple', ...) - pass symbol as positional arg
        3. add_item(symbol='AAPL', name='Apple', ...) - pass symbol as keyword arg
        """
        # Check if first argument is a WatchlistItem object
        if isinstance(symbol_or_item, WatchlistItem):
            item = symbol_or_item
            # Ensure added_date is set
            if not hasattr(item, 'added_date') or item.added_date is None:
                item.added_date = datetime.now()
        else:
            # Determine symbol from either positional or keyword argument
            symbol_value = symbol_or_item if symbol_or_item is not None else symbol
            if symbol_value is None:
                raise ValueError("Either pass a WatchlistItem object or provide a symbol")
            
            # Create new WatchlistItem from parameters
            item = WatchlistItem(
                symbol=symbol_value,
                name=name,
                asset_class=asset_class,
                category=category,
                added_date=datetime.now(),
                target_price=target_price,
                stop_loss=stop_loss,
                notes=notes,
                tags=tags or []
            )
        
        self.items[item.symbol] = item
        self._save_item(item)
        return item
    
    def remove_item(self, symbol: str) -> bool:
        """Remove item from watchlist"""
        if symbol in self.items:
            del self.items[symbol]
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
            return True
        return False
    
    def update_price(self, symbol: str, current_price: float) -> Optional[WatchlistItem]:
        """Update current price for item"""
        if symbol not in self.items:
            return None
        
        item = self.items[symbol]
        item.current_price = current_price
        self._save_item(item)
        return item
    
    def get_item(self, symbol: str) -> Optional[WatchlistItem]:
        """Get watchlist item by symbol"""
        return self.items.get(symbol)
    
    def get_by_category(self, category: WatchlistCategory) -> List[WatchlistItem]:
        """Get all items in a category"""
        return [item for item in self.items.values() if item.category == category]
    
    def get_by_asset_class(self, asset_class: AssetClass) -> List[WatchlistItem]:
        """Get all items of an asset class"""
        return [item for item in self.items.values() if item.asset_class == asset_class]
    
    def get_by_tag(self, tag: str) -> List[WatchlistItem]:
        """Get all items with a specific tag"""
        return [item for item in self.items.values() if tag in item.tags]
    
    def get_all(self) -> List[WatchlistItem]:
        """Get all watchlist items"""
        return list(self.items.values())
    
    def add_tag(self, symbol: str, tag: str) -> bool:
        """Add tag to watchlist item"""
        if symbol not in self.items:
            return False
        
        item = self.items[symbol]
        if tag not in item.tags:
            item.tags.append(tag)
            self._save_item(item)
        return True
    
    def remove_tag(self, symbol: str, tag: str) -> bool:
        """Remove tag from watchlist item"""
        if symbol not in self.items:
            return False
        
        item = self.items[symbol]
        if tag in item.tags:
            item.tags.remove(tag)
            self._save_item(item)
        return True
    
    def _save_item(self, item: WatchlistItem):
        """Save item to database"""
        tags_str = ",".join(item.tags) if item.tags else ""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO watchlist
                (symbol, name, asset_class, category, added_date, current_price, 
                 target_price, stop_loss, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.symbol,
                item.name,
                item.asset_class.value,
                item.category.value,
                item.added_date.isoformat(),
                item.current_price,
                item.target_price,
                item.stop_loss,
                item.notes,
                tags_str
            ))
    
    def _load_from_db(self):
        """Load watchlist from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM watchlist")
            for row in cursor:
                symbol, name, asset_class, category, added_date, current_price, \
                    target_price, stop_loss, notes, tags_str = row
                
                tags = tags_str.split(",") if tags_str else []
                
                item = WatchlistItem(
                    symbol=symbol,
                    name=name,
                    asset_class=AssetClass(asset_class),
                    category=WatchlistCategory(category),
                    added_date=datetime.fromisoformat(added_date),
                    current_price=current_price,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    notes=notes,
                    tags=tags
                )
                self.items[symbol] = item
    
    def get_summary(self) -> Dict:
        """Get watchlist summary"""
        categories = {}
        asset_classes = {}
        
        for item in self.items.values():
            # Count by category
            cat_name = item.category.value
            categories[cat_name] = categories.get(cat_name, 0) + 1
            
            # Count by asset class
            ac_name = item.asset_class.value
            asset_classes[ac_name] = asset_classes.get(ac_name, 0) + 1
        
        return {
            'total_items': len(self.items),
            'categories': categories,
            'asset_classes': asset_classes,
            'items': [
                {
                    'symbol': item.symbol,
                    'name': item.name,
                    'asset_class': item.asset_class.value,
                    'category': item.category.value,
                    'current_price': item.current_price,
                    'target_price': item.target_price,
                    'stop_loss': item.stop_loss,
                    'tags': item.tags
                }
                for item in sorted(self.items.values(), key=lambda x: x.symbol)
            ]
        }


class MultiWatchlist:
    """Manage multiple watchlists"""
    
    def __init__(self, db_path: str = "data/watchlists.db"):
        self.db_path = db_path
        self.watchlists: Dict[str, Watchlist] = {}
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize watchlist metadata database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist_meta (
                    name TEXT PRIMARY KEY,
                    created_date TEXT,
                    description TEXT
                )
            """)
    
    def create_watchlist(self, name: str, description: str = "") -> Watchlist:
        """Create a new watchlist"""
        watchlist = Watchlist(name=name)
        self.watchlists[name] = watchlist
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO watchlist_meta 
                (name, created_date, description)
                VALUES (?, ?, ?)
            """, (name, datetime.now().isoformat(), description))
        
        return watchlist
    
    def get_watchlist(self, name: str) -> Optional[Watchlist]:
        """Get watchlist by name"""
        if name not in self.watchlists:
            self.watchlists[name] = Watchlist(name=name)
        return self.watchlists[name]
    
    def list_watchlists(self) -> List[str]:
        """List all watchlist names"""
        return list(self.watchlists.keys())
