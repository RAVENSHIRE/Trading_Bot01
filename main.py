"""Main entry point for trading bot"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from config.logging_config import setup_logging
from src.core.portfolio import Portfolio
from src.data.ohlc_pipeline import OHLCPipeline
from src.signals.signal_generator import SignalGenerator
from src.risk.risk_manager import RiskManager
from src.watchlist.templates import populate_default_watchlists


def main():
    """Main trading bot execution"""
    
    # Setup
    logger = setup_logging()
    config = Config()
    
    logger.info("Starting Trading Bot...")
    logger.info(f"Initial Capital: ${config.get_int('default', 'INITIAL_CAPITAL')}")
    
    # Initialize components
    portfolio = Portfolio(
        initial_capital=config.get_int('default', 'INITIAL_CAPITAL')
    )
    data_pipeline = OHLCPipeline()
    signal_generator = SignalGenerator()
    risk_manager = RiskManager()
    
    logger.info("System initialized successfully")
    logger.info(f"Portfolio: {portfolio.get_summary({})}")
    
    # Initialize watchlists
    logger.info("Creating pre-populated watchlists...")
    watchlists = populate_default_watchlists()
    logger.info(f"✓ Created {len(watchlists)} watchlists with {sum(len(w.get_all()) for w in watchlists.values())} total symbols")
    
    # Fetch sample data
    symbols = ["AAPL", "MSFT", "GOOGL"]
    logger.info(f"Fetching data for {symbols}...")
    data_pipeline.fetch_and_store(symbols)
    
    logger.info("Trading bot ready")


if __name__ == "__main__":
    main()
