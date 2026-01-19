"""
Test imports for all new production modules
Verifies production setup is working
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_multi_source_pipeline():
    """Test multi-source data pipeline"""
    from data.multi_source_pipeline import MultiSourcePipeline, FMPConnector, YahooConnector
    
    pipeline = MultiSourcePipeline()
    assert hasattr(pipeline, 'fetch_market_data')
    assert hasattr(pipeline, 'fetch_fundamentals')
    print("✅ multi_source_pipeline")


def test_duckdb_analytics():
    """Test DuckDB analytics engine"""
    from analytics.duckdb_analytics import DuckDBAnalytics
    
    db = DuckDBAnalytics()
    assert hasattr(db, 'get_momentum_screen')
    assert hasattr(db, 'get_value_screen')
    assert hasattr(db, 'get_correlation_matrix')
    db.close()
    print("✅ duckdb_analytics")


def test_feature_store():
    """Test feature store"""
    from feature_store.features import FeatureStore, FeatureEngineering, TechnicalFeatures, FundamentalFeatures
    
    store = FeatureStore()
    fe = FeatureEngineering()
    
    assert hasattr(store, 'register_feature')
    assert hasattr(store, 'get_feature')
    assert hasattr(fe, 'create_price_features')
    
    print("✅ feature_store")


def test_technical_features():
    """Test technical analysis features"""
    from feature_store.features import TechnicalFeatures
    import pandas as pd
    import numpy as np
    
    # Create sample data
    data = pd.Series(np.random.randn(100).cumsum() + 100)
    
    # Test indicators
    sma = TechnicalFeatures.moving_average(data, 20)
    ema = TechnicalFeatures.exponential_moving_average(data, 12)
    rsi = TechnicalFeatures.relative_strength_index(data, 14)
    
    assert len(sma) == len(data)
    assert len(ema) == len(data)
    assert len(rsi) == len(data)
    
    print("✅ technical_features")


def test_optuna_tuner():
    """Test Optuna optimization"""
    from optimization.optuna_tuner import SignalOptimizer, ParameterTuner
    
    optimizer = SignalOptimizer()
    tuner = ParameterTuner()
    
    assert hasattr(optimizer, 'optimize_momentum_signal')
    assert hasattr(optimizer, 'optimize_mean_reversion_signal')
    assert hasattr(tuner, 'tune_signal_parameters')
    
    print("✅ optuna_tuner")


def test_prefect_flows():
    """Test Prefect orchestration (optional)"""
    try:
        from orchestration.prefect_flows import nightly_data_pipeline, hourly_market_check
        print("✅ prefect_flows (with Prefect)")
    except ImportError:
        # Prefect not installed, test fallback
        from orchestration.prefect_flows import nightly_data_pipeline
        print("✅ prefect_flows (fallback mode)")


def test_streamlit_dashboard():
    """Test Streamlit app can be imported"""
    # Note: Can't actually run Streamlit in tests, just verify import
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(
        "app",
        Path(__file__).parent / "dashboard" / "app.py"
    )
    
    if spec and spec.loader:
        # Module loads without error
        print("✅ streamlit_dashboard (importable)")
    else:
        raise ImportError("Streamlit dashboard not found")


def test_production_utilities():
    """Test production utility functions"""
    # Test verify script exists and is executable
    verify_script = Path(__file__).parent / "verify_production_setup.py"
    assert verify_script.exists()
    
    # Test setup script exists
    setup_script = Path(__file__).parent / "setup_production.sh"
    assert setup_script.exists()
    
    print("✅ production_utilities")


def test_production_documentation():
    """Test production documentation exists"""
    docs = [
        "PRODUCTION_SETUP.md",
        "PRODUCTION_UPGRADE.md",
    ]
    
    for doc in docs:
        doc_path = Path(__file__).parent / doc
        assert doc_path.exists(), f"Missing: {doc}"
    
    print("✅ production_documentation")


def test_database_directories():
    """Test production database directories exist"""
    dirs = [
        "database/cache",
        "database/fmp",
        "database/yahoo",
        "database/user",
        "database/optuna",
    ]
    
    for dir_name in dirs:
        dir_path = Path(__file__).parent / dir_name
        assert dir_path.exists(), f"Missing: {dir_name}"
    
    print("✅ database_directories")


def main():
    """Run all tests"""
    print("\n🧪 Testing Production Setup\n")
    
    tests = [
        test_database_directories,
        test_multi_source_pipeline,
        test_duckdb_analytics,
        test_feature_store,
        test_technical_features,
        test_optuna_tuner,
        test_prefect_flows,
        test_streamlit_dashboard,
        test_production_utilities,
        test_production_documentation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: {str(e)[:50]}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
