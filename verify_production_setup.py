#!/usr/bin/env python3
"""
Quick Start Script - Initialize Production Setup
Run all components and verify installation
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_dependencies():
    """Check if all required packages are installed"""
    logger.info("🔍 Checking dependencies...")
    
    required = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'yfinance': 'yfinance',
        'duckdb': 'duckdb',
        'optuna': 'optuna',
        'streamlit': 'streamlit',
        'plotly': 'plotly',
    }
    
    optional = {
        'prefect': 'prefect',
        'requests': 'requests',
    }
    
    missing = []
    for name, module in required.items():
        try:
            __import__(module)
            logger.info(f"✅ {name}")
        except ImportError:
            logger.error(f"❌ {name} not installed")
            missing.append(name)
    
    for name, module in optional.items():
        try:
            __import__(module)
            logger.info(f"✅ {name} (optional)")
        except ImportError:
            logger.warning(f"⚠️  {name} not installed (optional)")
    
    if missing:
        logger.error(f"\n❌ Missing required packages: {', '.join(missing)}")
        logger.info("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def test_multi_source_pipeline():
    """Test data pipeline"""
    logger.info("\n📊 Testing Multi-Source Data Pipeline...")
    
    try:
        from data.multi_source_pipeline import MultiSourcePipeline
        from datetime import datetime, timedelta
        
        pipeline = MultiSourcePipeline()
        
        # Test with small dataset
        symbols = ['AAPL']
        end = datetime.now()
        start = end - timedelta(days=5)
        
        market_data = pipeline.fetch_market_data(symbols, start, end)
        
        if not market_data.empty:
            logger.info(f"✅ Fetched {len(market_data)} market data points")
            logger.info(f"   Symbols: {market_data['Symbol'].unique()}")
            return True
        else:
            logger.error("❌ No market data returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing pipeline: {e}")
        return False


def test_duckdb_analytics():
    """Test DuckDB analytics"""
    logger.info("\n📈 Testing DuckDB Analytics...")
    
    try:
        from analytics.duckdb_analytics import DuckDBAnalytics
        import pandas as pd
        import numpy as np
        
        with DuckDBAnalytics() as db:
            # Create sample data
            dates = pd.date_range('2024-01-01', periods=10)
            sample = pd.DataFrame({
                'date': dates,
                'symbol': ['AAPL'] * 10,
                'open': np.random.rand(10) * 100,
                'high': np.random.rand(10) * 100,
                'low': np.random.rand(10) * 100,
                'close': range(150, 160),
                'volume': np.random.randint(1000000, 10000000, 10),
                'adj_close': range(150, 160)
            })
            
            db.insert_market_data(sample)
            logger.info("✅ DuckDB working")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error testing DuckDB: {e}")
        return False


def test_feature_store():
    """Test feature engineering"""
    logger.info("\n🔧 Testing Feature Store...")
    
    try:
        from feature_store.features import FeatureEngineering
        import pandas as pd
        import numpy as np
        
        fe = FeatureEngineering()
        
        # Create sample OHLCV
        dates = pd.date_range('2023-01-01', periods=100)
        ohlcv = pd.DataFrame({
            'date': dates,
            'open': 100 + np.cumsum(np.random.randn(100) * 2),
            'high': 102 + np.cumsum(np.random.randn(100) * 2),
            'low': 98 + np.cumsum(np.random.randn(100) * 2),
            'close': 100 + np.cumsum(np.random.randn(100) * 2),
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        features = fe.create_price_features(ohlcv)
        
        logger.info(f"✅ Generated {len(features.columns)} features")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing feature store: {e}")
        return False


def test_optuna_tuning():
    """Test optimization"""
    logger.info("\n🚀 Testing Optuna Optimization...")
    
    try:
        from optimization.optuna_tuner import ParameterTuner
        import pandas as pd
        import numpy as np
        
        tuner = ParameterTuner()
        
        # Create sample price data
        dates = pd.date_range('2023-01-01', periods=100)
        price_data = pd.DataFrame({
            'close': 100 + np.cumsum(np.random.randn(100) * 2),
            'high': 102 + np.cumsum(np.random.randn(100) * 2),
            'low': 98 + np.cumsum(np.random.randn(100) * 2),
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        # Quick test with 5 trials
        logger.info("   Running 5 optimization trials...")
        params = tuner.tune_signal_parameters("momentum", price_data, n_trials=5)
        
        logger.info(f"✅ Optimization working")
        logger.info(f"   Best Sharpe: {params.get('best_sharpe', 'N/A'):.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing optimization: {e}")
        return False


def verify_directories():
    """Verify all required directories exist"""
    logger.info("\n📁 Verifying directory structure...")
    
    dirs_to_check = [
        'database/cache',
        'database/fmp',
        'database/yahoo',
        'database/user',
        'database/optuna',
        'src/analytics',
        'src/feature_store',
        'src/optimization',
        'dashboard',
        'orchestration',
    ]
    
    base = Path(__file__).parent
    all_exist = True
    
    for dir_path in dirs_to_check:
        full_path = base / dir_path
        if full_path.exists():
            logger.info(f"✅ {dir_path}")
        else:
            logger.error(f"❌ {dir_path} missing")
            all_exist = False
    
    return all_exist


def show_summary(results):
    """Display test summary"""
    logger.info("\n" + "="*50)
    logger.info("PRODUCTION SETUP SUMMARY")
    logger.info("="*50)
    
    checks = [
        ("Dependencies", results['dependencies']),
        ("Directory Structure", results['directories']),
        ("Multi-Source Pipeline", results['pipeline']),
        ("DuckDB Analytics", results['duckdb']),
        ("Feature Store", results['features']),
        ("Optuna Optimization", results['optuna']),
    ]
    
    passed = 0
    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{name:.<30} {status}")
        if result:
            passed += 1
    
    logger.info("="*50)
    logger.info(f"Result: {passed}/{len(checks)} tests passed")
    
    if passed == len(checks):
        logger.info("\n🎉 Production setup complete! Ready to use.")
        logger.info("\nNext steps:")
        logger.info("1. Set FMP_API_KEY: export FMP_API_KEY=your_key")
        logger.info("2. Run dashboard: streamlit run dashboard/app.py")
        logger.info("3. Run data pipeline: python orchestration/prefect_flows.py")
    else:
        logger.warning("\n⚠️  Some tests failed. Check above for details.")


def main():
    """Main verification"""
    logger.info("🚀 Trading Bot Production Setup Verification\n")
    
    results = {
        'dependencies': check_dependencies(),
        'directories': verify_directories(),
        'pipeline': test_multi_source_pipeline(),
        'duckdb': test_duckdb_analytics(),
        'features': test_feature_store(),
        'optuna': test_optuna_tuning(),
    }
    
    show_summary(results)
    
    # Return appropriate exit code
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
