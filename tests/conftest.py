import sys
from pathlib import Path
import pytest
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise


@pytest.fixture
def watchlist(tmp_path):
    """Create a fresh watchlist for each test"""
    # Use a temporary database path for each test
    db_path = tmp_path / "test_watchlist.db"
    wl = Watchlist(name="Test Watchlist", db_path=str(db_path))
    
    # Add default test items using add_item() parameters
    wl.add_item(
        symbol='AAPL',
        name='Apple',
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM
    )
    wl.add_item(
        symbol='MSFT',
        name='Microsoft',
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.GROWTH
    )
    wl.add_item(
        symbol='GOOGL',
        name='Google',
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM
    )
    
    return wl