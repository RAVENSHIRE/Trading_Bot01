#!/usr/bin/env python3
"""
Initialize and configure data sources for the Trading Bot

Usage:
    python3 init_data_sources.py                 # Interactive setup
    python3 init_data_sources.py --validate      # Validate existing config
    python3 init_data_sources.py --test          # Test data fetching
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_sources_config import DataSourcesConfig, DataSourceType
from src.data.data_source_manager import DataSourceManager

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def interactive_setup():
    """Interactive setup wizard"""
    print_header("Trading Bot - Data Sources Setup Wizard")
    
    print("""
This wizard will help you configure data sources for the Trading Bot.

Data sources are used for:
  • Price Data (OHLCV)
  • Fundamentals (P/E, P/B, ROE, etc.)
  • Corporate Actions (dividends, splits)
  • Macro Data (economic indicators)

You can configure API keys for enhanced data access, or use the free
Yahoo Finance API that requires no authentication.
    """)
    
    api_keys = {}
    
    # FMP Setup
    print("\n1. FINANCIAL MODELING PREP (FMP)")
    print("-" * 40)
    print("   • Best for: Comprehensive financial data")
    print("   • Free tier: 250 calls/day")
    print("   • Sign up: https://financialmodelingprep.com")
    response = input("\n   Do you have an FMP API key? (y/n): ").strip().lower()
    if response == 'y':
        key = input("   Enter your FMP API key: ").strip()
        if key:
            api_keys['FMP_API_KEY'] = key
            print("   ✓ FMP API key saved")
    
    # Alpha Vantage Setup
    print("\n2. ALPHA VANTAGE")
    print("-" * 40)
    print("   • Best for: Intraday data, technical indicators")
    print("   • Free tier: 5 calls/minute")
    print("   • Sign up: https://www.alphavantage.co")
    response = input("\n   Do you have an Alpha Vantage API key? (y/n): ").strip().lower()
    if response == 'y':
        key = input("   Enter your Alpha Vantage API key: ").strip()
        if key:
            api_keys['ALPHA_VANTAGE_KEY'] = key
            print("   ✓ Alpha Vantage API key saved")
    
    # FRED Setup
    print("\n3. FRED (Federal Reserve Economic Data)")
    print("-" * 40)
    print("   • Best for: US economic indicators")
    print("   • Free: 120 calls/minute (unlimited data)")
    print("   • Sign up: https://fred.stlouisfed.org (free account)")
    response = input("\n   Do you have a FRED API key? (y/n): ").strip().lower()
    if response == 'y':
        key = input("   Enter your FRED API key: ").strip()
        if key:
            api_keys['FRED_API_KEY'] = key
            print("   ✓ FRED API key saved")
    
    # Quandl Setup
    print("\n4. QUANDL")
    print("-" * 40)
    print("   • Best for: Curated alternative data")
    print("   • Free tier: limited access")
    print("   • Sign up: https://www.quandl.com")
    response = input("\n   Do you have a Quandl API key? (y/n): ").strip().lower()
    if response == 'y':
        key = input("   Enter your Quandl API key: ").strip()
        if key:
            api_keys['QUANDL_API_KEY'] = key
            print("   ✓ Quandl API key saved")
    
    # Save to .env
    print_header("Saving Configuration")
    
    if api_keys:
        # Save to .env file
        env_file = Path(".env")
        with open(env_file, 'w') as f:
            for key, value in api_keys.items():
                f.write(f"{key}={value}\n")
        print(f"✓ API keys saved to .env")
        print(f"  Note: Add .env to .gitignore to keep keys secret!")
    else:
        print("✓ No API keys provided (using Yahoo Finance defaults)")
    
    # Set environment variables for this session
    for key, value in api_keys.items():
        os.environ[key] = value
    
    print("\n✓ Setup complete!")
    return api_keys


def validate_config():
    """Validate current configuration"""
    print_header("Validating Data Sources Configuration")
    
    print(DataSourcesConfig.get_configuration_summary())
    
    print("\nAPI Key Validation:")
    validation = DataSourcesConfig.validate_api_keys()
    all_valid = True
    for source, is_valid in validation.items():
        status = "✓" if is_valid else "✗"
        print(f"  {status} {source}")
        if not is_valid:
            all_valid = False
    
    if all_valid:
        print("\n✓ All API keys are configured!")
    else:
        print("\n⚠ Some API keys are missing (optional, will use fallback sources)")
    
    return all_valid


def test_fetching():
    """Test data fetching from configured sources"""
    print_header("Testing Data Fetching")
    
    manager = DataSourceManager(cache_enabled=False)
    
    # Test 1: Price Data
    print("\n1. Testing Price Data Fetching")
    print("-" * 40)
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        logger.info("Fetching AAPL price data (last 30 days)...")
        price_data = manager.fetch_price_data(
            symbols=['AAPL'],
            start_date=start_date,
            end_date=end_date,
            interval='1d'
        )
        
        if not price_data.empty:
            print(f"✓ Successfully fetched {len(price_data)} rows of price data")
            print(f"  Columns: {', '.join(price_data.columns.tolist())}")
        else:
            print("✗ Failed to fetch price data")
    except Exception as e:
        print(f"✗ Error fetching price data: {e}")
    
    # Test 2: Fundamentals
    print("\n2. Testing Fundamentals Fetching")
    print("-" * 40)
    try:
        logger.info("Fetching AAPL fundamentals...")
        fundamentals = manager.fetch_fundamentals(['AAPL'])
        
        if fundamentals and 'AAPL' in fundamentals:
            funda = fundamentals['AAPL']
            print("✓ Successfully fetched fundamentals")
            print(f"  P/E Ratio: {funda.get('pe_ratio', 'N/A')}")
            print(f"  P/B Ratio: {funda.get('pb_ratio', 'N/A')}")
            print(f"  ROE: {funda.get('roe', 'N/A')}")
        else:
            print("✗ Failed to fetch fundamentals")
    except Exception as e:
        print(f"✗ Error fetching fundamentals: {e}")
    
    # Test 3: Corporate Actions
    print("\n3. Testing Corporate Actions Fetching")
    print("-" * 40)
    try:
        logger.info("Fetching AAPL corporate actions...")
        actions = manager.fetch_corporate_actions(['AAPL'])
        
        if actions and 'AAPL' in actions:
            action_list = actions['AAPL']
            print(f"✓ Successfully fetched {len(action_list)} corporate actions")
            for action in action_list[:3]:
                print(f"  • {action['type'].upper()}: {action.get('date', 'N/A')}")
        else:
            print("✗ Failed to fetch corporate actions")
    except Exception as e:
        print(f"✗ Error fetching corporate actions: {e}")
    
    # Test 4: Macro Data
    print("\n4. Testing Macro Data Fetching")
    print("-" * 40)
    try:
        if os.getenv('FRED_API_KEY'):
            logger.info("Fetching GDP data from FRED...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365*5)
            
            macro_data = manager.fetch_macro_data(
                indicators=['GDP'],
                start_date=start_date,
                end_date=end_date
            )
            
            if macro_data and 'GDP' in macro_data:
                print(f"✓ Successfully fetched macro data")
                print(f"  GDP data points: {len(macro_data['GDP'])}")
            else:
                print("✗ Failed to fetch macro data (FRED API key required)")
        else:
            print("⊗ Skipped (FRED API key not configured)")
    except Exception as e:
        print(f"✗ Error fetching macro data: {e}")
    
    print("\n✓ Testing complete!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Initialize and configure data sources for Trading Bot'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate existing configuration'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test data fetching'
    )
    
    args = parser.parse_args()
    
    if args.validate:
        validate_config()
    elif args.test:
        validate_config()
        print()
        test_fetching()
    else:
        # Interactive setup
        api_keys = interactive_setup()
        print()
        validate_config()
        
        # Offer to test
        print("\n" + "=" * 60)
        response = input("Would you like to test data fetching now? (y/n): ").strip().lower()
        if response == 'y':
            print()
            test_fetching()


if __name__ == '__main__':
    main()
