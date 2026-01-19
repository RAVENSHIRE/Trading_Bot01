#!/usr/bin/env python3
"""
Data Sources Validation and Integration Test
Validates that all data sources are properly configured and working
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
logging.basicConfig(level=logging.INFO)

from data.data_sources_config import DataSourcesConfig, DataSourceType
from data.data_source_manager import DataSourceManager


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_environment_variables():
    """Check configured environment variables"""
    print_header("ENVIRONMENT VARIABLES")
    
    api_keys = {
        'FMP_API_KEY': 'Financial Modeling Prep',
        'ALPHA_VANTAGE_KEY': 'Alpha Vantage',
        'FRED_API_KEY': 'FRED (Federal Reserve)',
        'QUANDL_API_KEY': 'Quandl'
    }
    
    results = {}
    for env_var, name in api_keys.items():
        is_set = bool(os.getenv(env_var))
        results[env_var] = is_set
        status = "✓ SET" if is_set else "✗ NOT SET"
        print(f"  {status:12} {env_var:20} ({name})")
    
    return results


def check_data_sources_configuration():
    """Check data sources configuration"""
    print_header("DATA SOURCES CONFIGURATION")
    
    config_ok = True
    
    for source_type in DataSourceType:
        sources = DataSourcesConfig.get_sources_by_type(source_type)
        print(f"\n  {source_type.value.upper()}:")
        
        if not sources:
            print(f"    ✗ No enabled sources")
            config_ok = False
        else:
            for source in sources:
                has_key = "[API KEY SET]" if source.api_key else "[NO KEY]"
                status = "✓" if source.is_enabled else "✗"
                print(f"    {status} {source.name:30} {has_key:15} (Rate: {source.rate_limit}/min)")
    
    return config_ok


def check_directories():
    """Check required directories"""
    print_header("DIRECTORY STRUCTURE")
    
    dirs = {
        'data': Path('data'),
        'data/.cache': Path('data/.cache'),
        'data/fmp': Path('data/fmp'),
        'data/yahoo': Path('data/yahoo'),
        'logs': Path('logs'),
        'src/data': Path('src/data'),
        'database': Path('database')
    }
    
    all_exist = True
    for name, path in dirs.items():
        exists = path.exists()
        all_exist = all_exist and exists
        status = "✓" if exists else "✗"
        print(f"  {status} {name:20} {str(path)}")
    
    return all_exist


def check_databases():
    """Check database files"""
    print_header("DATABASE FILES")
    
    databases = {
        'OHLC': Path('data/ohlc_data.db'),
        'Fundamentals': Path('data/fundamentals_data.db'),
    }
    
    results = {}
    for name, path in databases.items():
        exists = path.exists()
        results[name] = exists
        status = "✓" if exists else "✗"
        size_str = f"({path.stat().st_size / 1024:.1f} KB)" if exists else ""
        print(f"  {status} {name:15} {path} {size_str}")
    
    return results


def check_cache():
    """Check cache status"""
    print_header("CACHE STATUS")
    
    cache_dir = Path('data/.cache')
    
    if not cache_dir.exists():
        print("  ✗ Cache directory not found")
        return False
    
    cache_files = list(cache_dir.glob('*.pkl'))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    print(f"  Cache directory: {cache_dir}")
    print(f"  Files: {len(cache_files)}")
    print(f"  Size: {total_size / (1024 * 1024):.2f} MB")
    
    return True


def test_yahoo_finance():
    """Test Yahoo Finance connectivity"""
    print_header("TESTING YAHOO FINANCE")
    
    try:
        manager = DataSourceManager(cache_enabled=False)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        print("  Fetching 5 days of AAPL data...")
        data = manager.fetch_price_data(['AAPL'], start_date, end_date)
        
        if not data.empty:
            print(f"  ✓ SUCCESS: Retrieved {len(data)} rows")
            print(f"    Date range: {data.index.min()} to {data.index.max()}")
            print(f"    Columns: {', '.join(data.columns.tolist())}")
            return True
        else:
            print("  ✗ FAILED: No data returned")
            return False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False


def test_fmp():
    """Test FMP connectivity"""
    print_header("TESTING FINANCIAL MODELING PREP (FMP)")
    
    if not os.getenv('FMP_API_KEY'):
        print("  ⊘ SKIPPED: FMP_API_KEY not configured")
        return None
    
    try:
        manager = DataSourceManager(cache_enabled=False)
        
        print("  Fetching AAPL fundamentals...")
        fundamentals = manager.fetch_fundamentals(['AAPL'])
        
        if fundamentals and 'AAPL' in fundamentals:
            data = fundamentals['AAPL']
            print(f"  ✓ SUCCESS: Retrieved {len(data)} metrics")
            for key, value in list(data.items())[:3]:
                print(f"    {key}: {value}")
            return True
        else:
            print("  ✗ FAILED: No fundamentals returned")
            return False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False


def test_corporate_actions():
    """Test corporate actions"""
    print_header("TESTING CORPORATE ACTIONS")
    
    try:
        manager = DataSourceManager(cache_enabled=False)
        
        print("  Fetching corporate actions for dividend stocks...")
        actions = manager.fetch_corporate_actions(['JNJ', 'KO', 'PG'])
        
        total_actions = sum(len(v) for v in actions.values())
        
        if total_actions > 0:
            print(f"  ✓ SUCCESS: Retrieved {total_actions} corporate actions")
            for symbol, action_list in actions.items():
                if action_list:
                    print(f"    {symbol}: {len(action_list)} actions")
            return True
        else:
            print("  ✗ FAILED: No corporate actions returned")
            return False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False


def test_macro_data():
    """Test macro data"""
    print_header("TESTING MACRO DATA (FRED)")
    
    if not os.getenv('FRED_API_KEY'):
        print("  ⊘ SKIPPED: FRED_API_KEY not configured")
        return None
    
    try:
        manager = DataSourceManager(cache_enabled=False)
        
        print("  Fetching GDP data...")
        start_date = datetime.now() - timedelta(days=365*10)
        end_date = datetime.now()
        
        macro = manager.fetch_macro_data(['GDP'], start_date, end_date)
        
        if macro and 'GDP' in macro:
            print(f"  ✓ SUCCESS: Retrieved macro data")
            df = macro['GDP']
            print(f"    Records: {len(df)}")
            return True
        else:
            print("  ✗ FAILED: No macro data returned")
            return False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False


def generate_report():
    """Generate comprehensive validation report"""
    print_header("GENERATING VALIDATION REPORT")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'environment': check_environment_variables(),
        'directories': {},
        'tests': {}
    }
    
    # Save report
    report_path = Path("logs/data_sources_validation_report.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"  ✓ Report saved to {report_path}")


def main():
    """Run all validation checks"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "DATA SOURCES VALIDATION SUITE" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Check configuration
    check_environment_variables()
    config_ok = check_data_sources_configuration()
    dirs_ok = check_directories()
    db_results = check_databases()
    check_cache()
    
    # Test connectivity
    print("\n" + "=" * 70)
    print("  CONNECTIVITY TESTS")
    print("=" * 70)
    
    results = {
        'Yahoo Finance': test_yahoo_finance(),
        'FMP': test_fmp(),
        'Corporate Actions': test_corporate_actions(),
        'Macro Data': test_macro_data(),
    }
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    print("\nConfiguration:")
    print(f"  {'✓' if config_ok else '✗'} Data sources configured")
    print(f"  {'✓' if dirs_ok else '✗'} Directories setup")
    print(f"  {'✓' if all(db_results.values()) else '✗'} Databases present")
    
    print("\nConnectivity Tests:")
    for test_name, result in results.items():
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✓ PASSED"
        else:
            status = "✗ FAILED"
        print(f"  {status:12} {test_name}")
    
    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    # Generate report
    generate_report()
    
    print("\n" + "=" * 70)
    print("  VALIDATION COMPLETE")
    print("=" * 70 + "\n")
    
    # Recommendations
    print("NEXT STEPS:")
    print("-" * 70)
    
    if not all(results.values()):
        print("1. Check failed connectivity tests")
        print("2. Verify API keys are set correctly")
        print("3. Check internet connection")
    
    if not config_ok:
        print("4. Review DATA_SOURCES_CONFIGURATION.md")
    
    if not dirs_ok:
        print("5. Run: python setup_data_sources.py")
    
    print("\nFor more information, see:")
    print("  - DATA_SOURCES_CONFIGURATION.md")
    print("  - examples_data_sources.py")
    print("  - logs/data_sources_validation_report.json")
    print()


if __name__ == "__main__":
    main()
