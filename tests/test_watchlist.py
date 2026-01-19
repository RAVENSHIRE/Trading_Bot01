"""Tests for watchlist module"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory, WatchlistItem


def test_watchlist_creation(tmp_path):
    """Test watchlist creation"""
    db_path = tmp_path / "test.db"
    watchlist = Watchlist(name="Test Watchlist", db_path=str(db_path))
    assert watchlist.name == "Test Watchlist"
    assert len(watchlist.get_all()) == 0


def test_add_item(tmp_path):
    """Test adding item to watchlist"""
    db_path = tmp_path / "test.db"
    watchlist = Watchlist(name="Test", db_path=str(db_path))
    
    item = watchlist.add_item(
        symbol="AAPL",
        name="Apple Inc.",
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM,
        target_price=160.0,
        stop_loss=140.0,
        tags=["Tech", "Large-Cap"]
    )
    
    assert item.symbol == "AAPL"
    assert item.name == "Apple Inc."
    assert len(watchlist.get_all()) == 1


def test_remove_item(tmp_path):
    """Test removing item from watchlist"""
    db_path = tmp_path / "test.db"
    watchlist = Watchlist(name="Test", db_path=str(db_path))
    watchlist.add_item(
        symbol="AAPL",
        name="Apple Inc.",
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM
    )
    
    assert len(watchlist.get_all()) == 1
    watchlist.remove_item("AAPL")
    assert len(watchlist.get_all()) == 0


def test_update_price(tmp_path):
    """Test updating item price"""
    db_path = tmp_path / "test.db"
    watchlist = Watchlist(name="Test", db_path=str(db_path))
    watchlist.add_item(
        symbol="AAPL",
        name="Apple Inc.",
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM
    )
    
    item = watchlist.update_price("AAPL", 155.0)
    assert item.current_price == 155.0


def test_get_by_category(tmp_path):
    """Test filtering by category"""
    db_path = tmp_path / "test.db"
    watchlist = Watchlist(name="Test", db_path=str(db_path))
    
    watchlist.add_item("AAPL", "Apple", AssetClass.STOCK, WatchlistCategory.MOMENTUM)
    watchlist.add_item("MSFT", "Microsoft", AssetClass.STOCK, WatchlistCategory.GROWTH)
    watchlist.add_item("GOOGL", "Google", AssetClass.STOCK, WatchlistCategory.MOMENTUM)
    
    momentum_items = watchlist.get_by_category(WatchlistCategory.MOMENTUM)
    assert len(momentum_items) == 2


def test_get_by_asset_class(watchlist):
    """Test filtering by asset class"""
    # Add test data with different asset classes
    watchlist.add_item(WatchlistItem(
        symbol='BND',
        name='Vanguard Total Bond',
        asset_class=AssetClass.BOND,  # Different asset class
        category=WatchlistCategory.INCOME
    ))
    
    # Now filter by STOCK - should get 3 items
    stocks = watchlist.get_by_asset_class(AssetClass.STOCK)
    assert len(stocks) == 3  # AAPL, MSFT, GOOGL
    
    # Filter by BOND - should get 1 item
    bonds = watchlist.get_by_asset_class(AssetClass.BOND)
    assert len(bonds) == 1  # BND


def test_tags(tmp_path):
    """Test tag functionality"""
    db_path = tmp_path / "test.db"
    watchlist = Watchlist(name="Test", db_path=str(db_path))
    watchlist.add_item(
        symbol="AAPL",
        name="Apple Inc.",
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM,
        tags=["Tech"]
    )
    
    watchlist.add_tag("AAPL", "Large-Cap")
    apple = watchlist.get_item("AAPL")
    assert "Large-Cap" in apple.tags
    
    tagged_items = watchlist.get_by_tag("Tech")
    assert len(tagged_items) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
