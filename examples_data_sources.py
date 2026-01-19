"""
Example: Using Data Sources in Trading Bot

This script demonstrates how to use the data source manager
to fetch price data, fundamentals, corporate actions, and macro data.

Run with: python3 examples_data_sources.py
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import DataSourceManager, DataSourcesConfig


def example_1_price_data():
    """Example 1: Fetch historical price data"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Fetching Historical Price Data")
    print("=" * 60)
    
    manager = DataSourceManager(cache_enabled=True)
    
    # Define date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\nFetching price data from {start_date.date()} to {end_date.date()}")
    print("Symbols: AAPL, MSFT, GOOGL")
    
    # Fetch data
    price_data = manager.fetch_price_data(
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        start_date=start_date,
        end_date=end_date,
        interval='1d'
    )
    
    if not price_data.empty:
        print(f"\n✓ Successfully fetched {len(price_data)} rows")
        print(f"  Columns: {', '.join(price_data.columns.tolist())}")
        print("\nFirst 5 rows:")
        print(price_data.head())
        print("\nLast 5 rows:")
        print(price_data.tail())
    else:
        print("\n✗ Failed to fetch price data")


def example_2_fundamentals():
    """Example 2: Fetch company fundamentals"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Fetching Company Fundamentals")
    print("=" * 60)
    
    manager = DataSourceManager(cache_enabled=True)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'JPM']
    print(f"\nFetching fundamentals for: {', '.join(symbols)}")
    
    # Fetch fundamentals
    fundamentals = manager.fetch_fundamentals(symbols)
    
    if fundamentals:
        print(f"\n✓ Retrieved fundamentals for {len(fundamentals)} companies")
        
        print("\nFundamental Metrics:")
        print("-" * 60)
        print(f"{'Symbol':<10} {'P/E Ratio':<12} {'P/B Ratio':<12} {'ROE':<12} {'Div Yield':<12}")
        print("-" * 60)
        
        for symbol, data in fundamentals.items():
            pe = data.get('pe_ratio', 'N/A')
            pb = data.get('pb_ratio', 'N/A')
            roe = data.get('roe', 'N/A')
            div = data.get('dividend_yield', 'N/A')
            
            if isinstance(pe, (int, float)):
                pe = f"{pe:.2f}"
            if isinstance(pb, (int, float)):
                pb = f"{pb:.2f}"
            if isinstance(roe, (int, float)):
                roe = f"{roe:.2%}"
            if isinstance(div, (int, float)):
                div = f"{div:.2%}"
            
            print(f"{symbol:<10} {str(pe):<12} {str(pb):<12} {str(roe):<12} {str(div):<12}")
        
        # Find value stocks (low P/E, low P/B)
        print("\n\nValue Stocks (P/E < 20 and P/B < 3):")
        print("-" * 40)
        found_any = False
        for symbol, data in fundamentals.items():
            pe = data.get('pe_ratio', float('inf'))
            pb = data.get('pb_ratio', float('inf'))
            if isinstance(pe, (int, float)) and isinstance(pb, (int, float)):
                if pe < 20 and pb < 3:
                    print(f"  ✓ {symbol}: P/E={pe:.2f}, P/B={pb:.2f}")
                    found_any = True
        
        if not found_any:
            print("  (No value stocks found in this set)")
    else:
        print("\n✗ Failed to fetch fundamentals")


def example_3_corporate_actions():
    """Example 3: Fetch corporate actions (dividends, splits)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Corporate Actions (Dividends & Splits)")
    print("=" * 60)
    
    manager = DataSourceManager(cache_enabled=True)
    
    symbols = ['AAPL', 'MSFT', 'JNJ', 'KO', 'PG']
    print(f"\nFetching corporate actions for: {', '.join(symbols)}")
    
    # Fetch corporate actions
    actions = manager.fetch_corporate_actions(symbols)
    
    if actions:
        print(f"\n✓ Retrieved corporate actions for {len(actions)} companies")
        
        # Dividends
        print("\n\nRecent Dividends:")
        print("-" * 60)
        dividend_count = 0
        for symbol, action_list in actions.items():
            dividends = [a for a in action_list if a['type'] == 'dividend']
            if dividends:
                total_dividend = sum(a.get('amount', 0) for a in dividends)
                print(f"  {symbol}: {len(dividends)} dividends, total: ${total_dividend:.2f}")
                dividend_count += len(dividends)
        
        if dividend_count == 0:
            print("  (No recent dividends found)")
        
        # Splits
        print("\n\nStock Splits:")
        print("-" * 60)
        split_count = 0
        for symbol, action_list in actions.items():
            splits = [a for a in action_list if a['type'] == 'split']
            if splits:
                for split in splits:
                    ratio = split.get('ratio', 'N/A')
                    date = split.get('date', 'N/A')
                    print(f"  {symbol}: {ratio}:1 split on {date}")
                    split_count += 1
        
        if split_count == 0:
            print("  (No stock splits found)")
    else:
        print("\n✗ Failed to fetch corporate actions")


def example_4_macro_data():
    """Example 4: Fetch economic indicators"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Macro Data (Economic Indicators)")
    print("=" * 60)
    
    manager = DataSourceManager(cache_enabled=True)
    
    # Check if FRED API key is set
    if not os.getenv('FRED_API_KEY'):
        print("\n⚠ FRED_API_KEY not set")
        print("  To fetch macro data, set: export FRED_API_KEY='your_key'")
        print("  Get free key at: https://fred.stlouisfed.org")
        return
    
    # Define date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)  # 5 years
    
    indicators = [
        'GDP',          # US Gross Domestic Product
        'UNRATE',       # Unemployment Rate
        'CPIAUCSL',     # Consumer Price Index
        'DGS10',        # 10-Year Treasury Yield
        'FEDFUNDS',     # Federal Funds Rate
    ]
    
    print(f"\nFetching economic indicators from {start_date.date()} to {end_date.date()}")
    print(f"Indicators: {', '.join(indicators)}")
    
    # Fetch macro data
    macro_data = manager.fetch_macro_data(
        indicators=indicators,
        start_date=start_date,
        end_date=end_date
    )
    
    if macro_data:
        print(f"\n✓ Retrieved {len(macro_data)} indicators")
        
        print("\nEconomic Indicators Summary:")
        print("-" * 60)
        
        for indicator, df in macro_data.items():
            if not df.empty:
                # Get latest value
                latest = df.iloc[-1]
                value = latest.get('value', latest.get('VALUE', 'N/A'))
                date = latest.get('date', latest.get('DATE', 'N/A'))
                
                print(f"  {indicator:<12}: {value:<12} (as of {date})")
                print(f"  {'  Data points':<12}: {len(df)}")
            else:
                print(f"  {indicator}: No data")
    else:
        print("\n✗ Failed to fetch macro data")


def example_5_configuration():
    """Example 5: Check data sources configuration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Data Sources Configuration")
    print("=" * 60)
    
    print(DataSourcesConfig.get_configuration_summary())
    
    print("\n\nAPI Key Status:")
    print("-" * 60)
    validation = DataSourcesConfig.validate_api_keys()
    for source, has_key in validation.items():
        status = "✓ Configured" if has_key else "✗ Not configured"
        print(f"  {source:<30}: {status}")


def example_6_caching():
    """Example 6: Demonstrate caching benefits"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Caching Benefits")
    print("=" * 60)
    
    import time
    
    symbols = ['AAPL', 'MSFT']
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    # First call - no cache
    print("\nFirst call (cache miss - actual API call)...")
    manager = DataSourceManager(cache_enabled=True)
    
    start_time = time.time()
    df1 = manager.fetch_price_data(symbols, start_date, end_date)
    first_duration = time.time() - start_time
    
    print(f"  Fetched {len(df1)} rows in {first_duration:.2f} seconds")
    
    # Second call - cache hit
    print("\nSecond call (cache hit - from disk)...")
    start_time = time.time()
    df2 = manager.fetch_price_data(symbols, start_date, end_date)
    second_duration = time.time() - start_time
    
    print(f"  Fetched {len(df2)} rows in {second_duration:.2f} seconds")
    
    speedup = first_duration / second_duration if second_duration > 0 else float('inf')
    print(f"\n✓ Speedup: {speedup:.1f}x faster with caching")
    print(f"  Cache location: data/.cache/")


def example_7_fallback_sources():
    """Example 7: Fallback sources when primary fails"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Fallback Sources")
    print("=" * 60)
    
    from src.data import DataSourceType
    
    print("\nData Source Hierarchy (fallback order):\n")
    
    for data_type in DataSourceType:
        sources = DataSourcesConfig.get_sources_by_type(data_type)
        print(f"{data_type.value.upper()}:")
        for i, source in enumerate(sources, 1):
            status = "✓" if source.is_enabled else "✗"
            print(f"  {i}. {status} {source.name}")
        print()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("TRADING BOT - DATA SOURCES EXAMPLES")
    print("=" * 60)
    
    examples = [
        ("1", "Price Data", example_1_price_data),
        ("2", "Fundamentals", example_2_fundamentals),
        ("3", "Corporate Actions", example_3_corporate_actions),
        ("4", "Macro Data", example_4_macro_data),
        ("5", "Configuration", example_5_configuration),
        ("6", "Caching", example_6_caching),
        ("7", "Fallback Sources", example_7_fallback_sources),
    ]
    
    # Check if specific example requested
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        for num, name, func in examples:
            if num == example_num:
                func()
                return
        print(f"\n✗ Example {example_num} not found")
        return
    
    # Run all examples
    for num, name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error in example {num} ({name}): {e}")
    
    print("\n" + "=" * 60)
    print("✓ All examples completed!")
    print("=" * 60)
    print("\nRun specific examples with:")
    print("  python3 examples_data_sources.py 1  # Price Data")
    print("  python3 examples_data_sources.py 2  # Fundamentals")
    print("  python3 examples_data_sources.py 3  # Corporate Actions")
    print("  python3 examples_data_sources.py 4  # Macro Data")
    print("  python3 examples_data_sources.py 5  # Configuration")
    print("  python3 examples_data_sources.py 6  # Caching")
    print("  python3 examples_data_sources.py 7  # Fallback Sources")


if __name__ == '__main__':
    main()
