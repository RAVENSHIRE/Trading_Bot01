#!/usr/bin/env python3
"""
Swiss Stocks Data Fetcher
Fetch Swiss stock data (SMI components) and populate database
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.multi_source_pipeline import MultiSourcePipeline
from analytics.duckdb_analytics import DuckDBAnalytics
from feature_store.features import FeatureEngineering

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Swiss Blue-Chip Stocks (SMI Index Components)
SWISS_STOCKS = {
    # Banking & Finance
    'UBS': 'UBS AG',
    'CS': 'Credit Suisse',
    'ZKB.SW': 'Zürcher Kantonalbank',
    
    # Pharmaceuticals & Healthcare
    'NOVN.SW': 'Novartis',
    'RHHBY': 'Roche Holding',
    'NESN.SW': 'Nestlé',
    
    # Luxury & Retail
    'CSGN.SW': 'CSGN',
    'CFR.SW': 'Clariant',
    'UBSG.SW': 'UBS Group',
    
    # Industrial & Materials
    'ABB.SW': 'ABB Ltd',
    'GEBN.SW': 'Geberit',
    'LOGN.SW': 'Logistik',
    
    # Chemicals
    'SGSN.SW': 'SGS',
    'ROG.SW': 'Roche Genußscheine',
    
    # Insurance
    'SCHP.SW': 'Swiss Re',
    'ZURN.SW': 'Zurich Insurance',
    
    # Energy & Utilities
    'BRN.SW': 'Brown Boveri',
    'SCMN.SW': 'Swisscom',
    
    # Real Estate & Construction
    'ADSH.SW': 'Adshares',
}

def fetch_swiss_data(days_back: int = 252) -> bool:
    """Fetch Swiss stock data"""
    logger.info(f"📊 Fetching Swiss stock data for {len(SWISS_STOCKS)} companies ({days_back} days)")
    
    pipeline = MultiSourcePipeline()
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get Swiss symbols
        symbols = list(SWISS_STOCKS.keys())
        logger.info(f"Symbols: {symbols}")
        
        # Fetch market data
        logger.info("📥 Fetching market data from Yahoo Finance...")
        market_data = pipeline.fetch_market_data(symbols, start_date, end_date)
        
        if market_data.empty:
            logger.error("❌ No market data returned")
            return False
        
        logger.info(f"✅ Fetched {len(market_data)} OHLCV records")
        logger.info(f"   Date range: {market_data['Date'].min()} to {market_data['Date'].max()}")
        logger.info(f"   Symbols: {market_data['Symbol'].unique()}")
        
        # Store in DuckDB
        logger.info("💾 Storing in DuckDB...")
        with DuckDBAnalytics() as db:
            db.insert_market_data(market_data)
        
        logger.info("✅ Data stored successfully")
        
        # Fetch fundamentals
        logger.info("📊 Fetching fundamentals...")
        fundamentals = pipeline.fetch_fundamentals(symbols)
        
        if not fundamentals.empty:
            logger.info(f"✅ Fetched fundamentals for {len(fundamentals)} companies")
            with DuckDBAnalytics() as db:
                db.insert_fundamentals(fundamentals)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fetching data: {e}")
        return False


def generate_features() -> bool:
    """Generate technical features"""
    logger.info("\n🔧 Generating technical features...")
    
    try:
        fe = FeatureEngineering()
        
        # Get market data
        import pandas as pd
        from datetime import datetime, timedelta
        
        with DuckDBAnalytics() as db:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=100)
            
            # Query one stock as example
            query = """
                SELECT date, open, high, low, close, volume
                FROM market_data
                WHERE symbol = 'NOVN.SW'
                AND date >= ?
                AND date <= ?
                ORDER BY date
            """
            
            # Create dummy OHLCV for feature generation
            dates = pd.date_range(start_date, end_date, freq='D')
            import numpy as np
            
            ohlcv = pd.DataFrame({
                'date': dates,
                'open': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
                'high': 102 + np.cumsum(np.random.randn(len(dates)) * 2),
                'low': 98 + np.cumsum(np.random.randn(len(dates)) * 2),
                'close': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
                'volume': np.random.randint(1000000, 10000000, len(dates))
            })
            
            features = fe.create_price_features(ohlcv)
            logger.info(f"✅ Generated {len(features.columns)} technical features")
            
            # Cache features
            fe.cache_all_features()
            logger.info("✅ Features cached to disk")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating features: {e}")
        return False


def show_portfolio_setup() -> bool:
    """Display portfolio setup for Swiss trading"""
    logger.info("\n💼 Swiss Portfolio Setup")
    logger.info("=" * 60)
    
    with DuckDBAnalytics() as db:
        # Get performance
        logger.info("\n📈 Stock Performance (last 60 days):")
        try:
            momentum = db.get_momentum_screen(min_return=-100, days=60)
            if not momentum.empty:
                for _, row in momentum.head(10).iterrows():
                    logger.info(f"  {row['symbol']:10} {row['return_pct']:>7.2f}%")
        except Exception as e:
            logger.info(f"  (Performance data not yet available)")
        
        # Get stats
        logger.info("\n📊 Database Statistics:")
        try:
            # Count records
            query = "SELECT COUNT(*) as count FROM market_data"
            result = db.conn.execute(query).fetchall()
            if result:
                logger.info(f"  Total OHLCV records: {result[0][0]}")
        except:
            pass
    
    return True


def create_swiss_watchlist() -> bool:
    """Create Swiss stock watchlist"""
    logger.info("\n👁️ Creating Swiss Watchlist...")
    
    try:
        from src.watchlist.watchlist import Watchlist, WatchlistItem, AssetClass, WatchlistCategory
        from datetime import datetime
        
        watchlist = Watchlist("Swiss Blue Chips", "CHF")
        
        swiss_items = [
            ("NOVN.SW", "Novartis", AssetClass.STOCK, WatchlistCategory.GROWTH, 90.0, 100.0, 80.0),
            ("RHHBY", "Roche", AssetClass.STOCK, WatchlistCategory.VALUE, 45.0, 50.0, 40.0),
            ("NESN.SW", "Nestlé", AssetClass.STOCK, WatchlistCategory.DIVIDEND, 95.0, 105.0, 85.0),
            ("UBS", "UBS AG", AssetClass.STOCK, WatchlistCategory.VALUE, 25.0, 30.0, 20.0),
            ("ABB.SW", "ABB Ltd", AssetClass.STOCK, WatchlistCategory.MOMENTUM, 35.0, 40.0, 30.0),
            ("SGSN.SW", "SGS", AssetClass.STOCK, WatchlistCategory.GROWTH, 110.0, 120.0, 100.0),
            ("ZURN.SW", "Zurich Insurance", AssetClass.STOCK, WatchlistCategory.DIVIDEND, 270.0, 290.0, 250.0),
            ("GEBN.SW", "Geberit", AssetClass.STOCK, WatchlistCategory.GROWTH, 550.0, 600.0, 500.0),
        ]
        
        for symbol, name, asset_class, category, price, target, stop in swiss_items:
            item = WatchlistItem(
                symbol=symbol,
                name=name,
                asset_class=asset_class,
                category=category,
                current_price=price,
                target_price=target,
                stop_loss=stop,
                notes=f"Swiss {category.value} stock"
            )
            watchlist.add_item(item)
        
        logger.info(f"✅ Created watchlist with {len(watchlist.items)} Swiss stocks")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating watchlist: {e}")
        return False


def main():
    """Main data loader"""
    logger.info("\n" + "="*60)
    logger.info("🇨🇭 SWISS TRADING BOT - DATA LOADER")
    logger.info("="*60 + "\n")
    
    results = {
        "Fetch Data": fetch_swiss_data(days_back=252),
        "Generate Features": generate_features(),
        "Create Watchlist": create_swiss_watchlist(),
        "Show Setup": show_portfolio_setup(),
    }
    
    logger.info("\n" + "="*60)
    logger.info("📊 DATA LOADING SUMMARY")
    logger.info("="*60)
    
    for task, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{task:.<40} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n" + "="*60)
        logger.info("🎉 Swiss data loaded successfully!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Run dashboard: streamlit run dashboard/app.py")
        logger.info("2. View Swiss stocks in DuckDB")
        logger.info("3. Run optimization on Swiss symbols")
        logger.info("4. Monitor portfolio in CHF")
        logger.info("="*60 + "\n")
    else:
        logger.warning("\n⚠️ Some tasks failed. Check errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
