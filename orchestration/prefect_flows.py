"""
Prefect Orchestration Flows
Automated data pipelines and workflows
"""

from datetime import datetime, timedelta
from typing import List

try:
    from prefect import flow, task
    from prefect.schedules import IntervalSchedule
    PREFECT_AVAILABLE = True
except ImportError:
    PREFECT_AVAILABLE = False
    print("Warning: Prefect not installed. Flows will not be scheduled.")

import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.multi_source_pipeline import MultiSourcePipeline
from analytics.duckdb_analytics import DuckDBAnalytics
from feature_store.features import FeatureEngineering
from backtesting.backtest_engine import BacktestEngine

logger = logging.getLogger(__name__)


if PREFECT_AVAILABLE:
    
    @task(name="Fetch Market Data", retries=2)
    def fetch_market_data_task(symbols: List[str], days: int = 252):
        """Fetch market data from Yahoo Finance"""
        pipeline = MultiSourcePipeline()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching market data for {len(symbols)} symbols")
        market_data = pipeline.fetch_market_data(symbols, start_date, end_date)
        
        # Store in analytics
        analytics = DuckDBAnalytics()
        analytics.insert_market_data(market_data)
        analytics.close()
        
        logger.info(f"Stored {len(market_data)} market data points")
        return market_data
    
    
    @task(name="Fetch Fundamentals", retries=2)
    def fetch_fundamentals_task(symbols: List[str]):
        """Fetch company fundamentals"""
        pipeline = MultiSourcePipeline()
        
        logger.info(f"Fetching fundamentals for {len(symbols)} companies")
        fundamentals = pipeline.fetch_fundamentals(symbols)
        
        # Store in analytics
        analytics = DuckDBAnalytics()
        analytics.insert_fundamentals(fundamentals)
        analytics.close()
        
        logger.info(f"Stored {len(fundamentals)} fundamental records")
        return fundamentals
    
    
    @task(name="Generate Features")
    def generate_features_task(market_data):
        """Generate technical and fundamental features"""
        logger.info("Generating features")
        
        fe = FeatureEngineering()
        features = fe.create_price_features(market_data)
        
        # Cache features
        fe.cache_all_features()
        
        logger.info(f"Generated {len(features.columns)} features")
        return features
    
    
    @task(name="Backtest Signals")
    def backtest_signals_task():
        """Run backtests on existing signals"""
        logger.info("Running backtest")
        
        # This would connect to backtesting engine
        backtest = BacktestEngine()
        
        logger.info("Backtest complete")
        return {}
    
    
    @flow(name="nightly-data-pipeline", description="Daily market data refresh")
    def nightly_data_pipeline():
        """Nightly data collection and processing"""
        symbols = [
            "AAPL", "MSFT", "GOOGL", "NVDA", "META",
            "TSLA", "AMD", "AVGO", "JNJ", "PG"
        ]
        
        logger.info("Starting nightly data pipeline")
        
        # Fetch data
        market_data = fetch_market_data_task(symbols)
        fundamentals = fetch_fundamentals_task(symbols)
        
        # Generate features
        features = generate_features_task(market_data)
        
        logger.info("Nightly pipeline complete")
        return {"market_data": market_data, "features": features}
    
    
    @flow(name="nightly-signal-optimization", description="Daily signal parameter optimization")
    def nightly_signal_optimization():
        """Optimize signal parameters"""
        logger.info("Starting signal optimization")
        
        from optimization.optuna_tuner import ParameterTuner
        
        # Load recent data
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "META"]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=252)
        
        pipeline = MultiSourcePipeline()
        market_data = pipeline.fetch_market_data(symbols, start_date, end_date)
        
        # Optimize momentum signal
        tuner = ParameterTuner()
        momentum_params = tuner.tune_signal_parameters("momentum", market_data, n_trials=50)
        
        logger.info(f"Optimized momentum signal: {momentum_params}")
        
        return momentum_params
    
    
    @flow(name="hourly-market-check", description="Hourly market data check")
    def hourly_market_check():
        """Hourly market data refresh for live monitoring"""
        logger.info("Running hourly market check")
        
        key_symbols = ["SPY", "QQQ", "IWM"]
        
        pipeline = MultiSourcePipeline()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        market_data = pipeline.fetch_market_data(key_symbols, start_date, end_date)
        
        analytics = DuckDBAnalytics()
        momentum_stocks = analytics.get_momentum_screen(min_return=0.01, days=5)
        analytics.close()
        
        logger.info(f"Hourly check complete: {len(momentum_stocks)} momentum stocks found")
        
        return momentum_stocks


else:
    # Fallback functions without Prefect
    
    def fetch_market_data_task(symbols: List[str], days: int = 252):
        """Fetch market data from Yahoo Finance (no Prefect)"""
        pipeline = MultiSourcePipeline()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching market data for {len(symbols)} symbols")
        market_data = pipeline.fetch_market_data(symbols, start_date, end_date)
        
        analytics = DuckDBAnalytics()
        analytics.insert_market_data(market_data)
        analytics.close()
        
        return market_data
    
    
    def nightly_data_pipeline():
        """Nightly data collection (no Prefect)"""
        symbols = [
            "AAPL", "MSFT", "GOOGL", "NVDA", "META",
            "TSLA", "AMD", "AVGO", "JNJ", "PG"
        ]
        
        logger.info("Starting nightly data pipeline")
        market_data = fetch_market_data_task(symbols)
        logger.info("Nightly pipeline complete")
        
        return market_data


if __name__ == "__main__":
    # Manual execution
    if PREFECT_AVAILABLE:
        print("Running nightly data pipeline...")
        result = nightly_data_pipeline()
        print(f"Pipeline complete: {result}")
    else:
        print("Prefect not installed. Running fallback pipeline...")
        result = nightly_data_pipeline()
        print("Pipeline complete")
