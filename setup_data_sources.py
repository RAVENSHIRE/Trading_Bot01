#!/usr/bin/env python3
"""
Data Sources Setup and Configuration Script
Configures and initializes all data sources for the Trading Bot
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data.data_sources_config import DataSourcesConfig, DataSourceType
from data.data_source_manager import DataSourceManager
from data.ohlc_pipeline import OHLCPipeline
from data.fundamentals_pipeline import FundamentalsPipeline
from data.multi_source_pipeline import FMPConnector, YahooConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_sources_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataSourcesSetup:
    """Setup and configuration for all data sources"""
    
    def __init__(self):
        self.manager = DataSourceManager(cache_enabled=True)
        self.ohlc_pipeline = OHLCPipeline(db_path="data/ohlc_data.db")
        self.fundamentals_pipeline = FundamentalsPipeline(db_path="data/fundamentals_data.db")
        self.fmp_connector = FMPConnector()
        self.yahoo_connector = YahooConnector()
        
        # Create required directories
        Path("data").mkdir(exist_ok=True)
        Path("data/.cache").mkdir(exist_ok=True)
        Path("data/fmp").mkdir(exist_ok=True)
        Path("data/yahoo").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that all required API keys are set"""
        logger.info("=" * 60)
        logger.info("VALIDATING API KEYS")
        logger.info("=" * 60)
        
        validation = DataSourcesConfig.validate_api_keys()
        
        for source, is_valid in validation.items():
            status = "✓ READY" if is_valid else "✗ MISSING"
            logger.info(f"  {status}: {source}")
        
        return validation
    
    def print_configuration_summary(self):
        """Print summary of data sources configuration"""
        logger.info("=" * 60)
        logger.info("DATA SOURCES CONFIGURATION")
        logger.info("=" * 60)
        
        summary = DataSourcesConfig.get_configuration_summary()
        for line in summary.split('\n'):
            logger.info(line)
    
    def test_data_source_connectivity(self) -> Dict[str, bool]:
        """Test connectivity to all data sources"""
        logger.info("=" * 60)
        logger.info("TESTING DATA SOURCE CONNECTIVITY")
        logger.info("=" * 60)
        
        results = {}
        
        # Test Yahoo Finance
        try:
            logger.info("Testing Yahoo Finance...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            data = self.manager.fetch_price_data(['AAPL'], start_date, end_date)
            
            if not data.empty:
                logger.info("  ✓ Yahoo Finance: OK")
                results["Yahoo Finance"] = True
            else:
                logger.warning("  ✗ Yahoo Finance: No data returned")
                results["Yahoo Finance"] = False
        except Exception as e:
            logger.warning(f"  ✗ Yahoo Finance: {e}")
            results["Yahoo Finance"] = False
        
        # Test FMP if API key is set
        if os.getenv('FMP_API_KEY'):
            try:
                logger.info("Testing FMP...")
                profile = self.fmp_connector.get_company_profile('AAPL')
                
                if profile:
                    logger.info("  ✓ FMP: OK")
                    results["FMP"] = True
                else:
                    logger.warning("  ✗ FMP: No data returned")
                    results["FMP"] = False
            except Exception as e:
                logger.warning(f"  ✗ FMP: {e}")
                results["FMP"] = False
        else:
            logger.info("  ⊘ FMP: API key not configured")
            results["FMP"] = None
        
        # Test Alpha Vantage if API key is set
        if os.getenv('ALPHA_VANTAGE_KEY'):
            try:
                logger.info("Testing Alpha Vantage...")
                # Alpha Vantage has strict rate limits
                logger.info("  ⊘ Alpha Vantage: Skipped (rate limited)")
                results["Alpha Vantage"] = None
            except Exception as e:
                logger.warning(f"  ✗ Alpha Vantage: {e}")
                results["Alpha Vantage"] = False
        else:
            logger.info("  ⊘ Alpha Vantage: API key not configured")
            results["Alpha Vantage"] = None
        
        return results
    
    def initialize_databases(self):
        """Initialize all required databases"""
        logger.info("=" * 60)
        logger.info("INITIALIZING DATABASES")
        logger.info("=" * 60)
        
        try:
            # OHLC Database
            logger.info("Initializing OHLC database...")
            db_path = Path("data/ohlc_data.db")
            if db_path.exists():
                logger.info(f"  OHLC database already exists at {db_path}")
            else:
                self.ohlc_pipeline  # Initialization happens in __init__
                logger.info(f"  ✓ OHLC database initialized at {db_path}")
            
            # Fundamentals Database
            logger.info("Initializing Fundamentals database...")
            db_path = Path("data/fundamentals_data.db")
            if db_path.exists():
                logger.info(f"  Fundamentals database already exists at {db_path}")
            else:
                self.fundamentals_pipeline  # Initialization happens in __init__
                logger.info(f"  ✓ Fundamentals database initialized at {db_path}")
            
            logger.info("✓ All databases initialized successfully")
            
        except Exception as e:
            logger.error(f"✗ Database initialization failed: {e}")
            raise
    
    def fetch_initial_data(self, symbols: List[str] = None, days_back: int = 365):
        """Fetch initial price and fundamental data"""
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'V', 'WMT']
        
        logger.info("=" * 60)
        logger.info("FETCHING INITIAL DATA")
        logger.info("=" * 60)
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Period: Last {days_back} days")
        
        # Fetch price data
        try:
            logger.info("\nFetching price data...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            price_data = self.manager.fetch_price_data(symbols, start_date, end_date)
            
            if not price_data.empty:
                logger.info(f"  ✓ Fetched price data: {len(price_data)} rows")
                logger.info(f"    Columns: {list(price_data.columns)}")
            else:
                logger.warning("  ✗ No price data retrieved")
        
        except Exception as e:
            logger.error(f"  ✗ Error fetching price data: {e}")
        
        # Fetch fundamentals
        try:
            logger.info("\nFetching fundamentals...")
            fundamentals = self.manager.fetch_fundamentals(symbols)
            
            if fundamentals:
                logger.info(f"  ✓ Fetched fundamentals for {len(fundamentals)} symbols")
                for symbol, data in list(fundamentals.items())[:3]:
                    logger.info(f"    {symbol}: {len(data)} metrics")
            else:
                logger.warning("  ✗ No fundamentals retrieved")
        
        except Exception as e:
            logger.error(f"  ✗ Error fetching fundamentals: {e}")
        
        # Fetch corporate actions
        try:
            logger.info("\nFetching corporate actions...")
            actions = self.manager.fetch_corporate_actions(symbols)
            
            if actions:
                total_actions = sum(len(v) for v in actions.values())
                logger.info(f"  ✓ Fetched corporate actions: {total_actions} total")
                for symbol, data in list(actions.items())[:3]:
                    if data:
                        logger.info(f"    {symbol}: {len(data)} actions")
            else:
                logger.warning("  ✗ No corporate actions retrieved")
        
        except Exception as e:
            logger.error(f"  ✗ Error fetching corporate actions: {e}")
    
    def generate_setup_report(self) -> Dict:
        """Generate a comprehensive setup report"""
        logger.info("=" * 60)
        logger.info("GENERATING SETUP REPORT")
        logger.info("=" * 60)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'api_keys_configured': self.validate_api_keys(),
            'data_sources': self._get_data_sources_info(),
            'directories': self._check_directories(),
            'cache_status': self._check_cache_status()
        }
        
        # Save report
        report_path = Path("logs/data_sources_setup_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"✓ Setup report saved to {report_path}")
        
        return report
    
    def _get_data_sources_info(self) -> Dict:
        """Get information about configured data sources"""
        sources_info = {}
        
        for source_type in DataSourceType:
            sources = DataSourcesConfig.get_sources_by_type(source_type)
            sources_info[source_type.value] = [
                {
                    'name': s.name,
                    'enabled': s.is_enabled,
                    'rate_limit': s.rate_limit,
                    'cache_ttl_days': s.cache_ttl_days,
                    'has_api_key': bool(s.api_key)
                }
                for s in sources
            ]
        
        return sources_info
    
    def _check_directories(self) -> Dict[str, bool]:
        """Check if all required directories exist"""
        dirs = {
            'data': Path('data'),
            'data/.cache': Path('data/.cache'),
            'data/fmp': Path('data/fmp'),
            'data/yahoo': Path('data/yahoo'),
            'logs': Path('logs')
        }
        
        status = {}
        for name, path in dirs.items():
            status[name] = path.exists()
        
        return status
    
    def _check_cache_status(self) -> Dict:
        """Check cache status"""
        cache_dir = Path('data/.cache')
        
        if not cache_dir.exists():
            return {'exists': False, 'files': 0, 'size_mb': 0}
        
        cache_files = list(cache_dir.glob('*.pkl'))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'exists': True,
            'files': len(cache_files),
            'size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def run_full_setup(self, 
                      test_connectivity: bool = True,
                      fetch_initial_data: bool = True,
                      symbols: List[str] = None,
                      days_back: int = 365):
        """Run complete setup process"""
        logger.info("\n" + "=" * 60)
        logger.info("TRADING BOT DATA SOURCES SETUP")
        logger.info("=" * 60 + "\n")
        
        try:
            # Step 1: Validate API keys
            self.validate_api_keys()
            
            # Step 2: Print configuration
            self.print_configuration_summary()
            
            # Step 3: Initialize databases
            self.initialize_databases()
            
            # Step 4: Test connectivity
            if test_connectivity:
                self.test_data_source_connectivity()
            
            # Step 5: Fetch initial data
            if fetch_initial_data:
                self.fetch_initial_data(symbols, days_back)
            
            # Step 6: Generate report
            self.generate_setup_report()
            
            logger.info("\n" + "=" * 60)
            logger.info("✓ DATA SOURCES SETUP COMPLETED SUCCESSFULLY")
            logger.info("=" * 60 + "\n")
            
        except Exception as e:
            logger.error(f"\n✗ SETUP FAILED: {e}")
            raise


def print_usage():
    """Print usage instructions"""
    usage = """
Data Sources Setup Script
========================

Usage: python setup_data_sources.py [options]

Options:
  --help              Show this help message
  --quick             Quick setup (no data fetch)
  --full              Full setup with data fetch (default)
  --symbols SYMBOLS   Comma-separated list of symbols (default: AAPL, MSFT, etc.)
  --days DAYS         Days of historical data to fetch (default: 365)
  --no-test           Skip connectivity tests
  --no-data           Skip initial data fetch

Environment Variables:
  FMP_API_KEY         Financial Modeling Prep API key
  ALPHA_VANTAGE_KEY   Alpha Vantage API key
  FRED_API_KEY        Federal Reserve Economic Data API key
  QUANDL_API_KEY      Quandl API key

Examples:
  python setup_data_sources.py --full
  python setup_data_sources.py --quick
  python setup_data_sources.py --symbols AAPL,MSFT,GOOGL --days 90
"""
    print(usage)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Trading Bot Data Sources')
    parser.add_argument('--quick', action='store_true', help='Quick setup without data fetch')
    parser.add_argument('--symbols', help='Comma-separated symbols to fetch')
    parser.add_argument('--days', type=int, default=365, help='Days of historical data')
    parser.add_argument('--no-test', action='store_true', help='Skip connectivity tests')
    parser.add_argument('--no-data', action='store_true', help='Skip data fetch')
    
    args = parser.parse_args()
    
    setup = DataSourcesSetup()
    
    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]
    
    # Run setup
    setup.run_full_setup(
        test_connectivity=not args.no_test and not args.quick,
        fetch_initial_data=not args.no_data and not args.quick,
        symbols=symbols,
        days_back=args.days
    )
