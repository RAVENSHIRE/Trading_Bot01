# Data Sources Integration Guide

## Integration with Trading Bot Strategy

This guide shows how to integrate the configured data sources into your trading strategies.

## 1. Basic Integration Pattern

```python
from src.data.data_source_manager import DataSourceManager
from src.data.ohlc_pipeline import OHLCPipeline
from src.data.fundamentals_pipeline import FundamentalsPipeline
from datetime import datetime, timedelta

class StrategyWithDataSources:
    def __init__(self):
        # Initialize data sources
        self.manager = DataSourceManager(cache_enabled=True)
        self.ohlc_db = OHLCPipeline()
        self.fundamentals_db = FundamentalsPipeline()
    
    def prepare_data(self, symbols: List[str], days: int = 365):
        """Prepare all required data"""
        
        # Fetch price data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        prices = self.manager.fetch_price_data(symbols, start_date, end_date)
        
        # Fetch fundamentals
        fundamentals = self.manager.fetch_fundamentals(symbols)
        
        # Fetch corporate actions for adjustments
        actions = self.manager.fetch_corporate_actions(symbols)
        
        return prices, fundamentals, actions
```

## 2. Trading Signal Integration

### Example: Value + Quality Screen

```python
from src.signals.signal_generator import SignalGenerator

class ValueQualityStrategy(SignalGenerator):
    def __init__(self):
        super().__init__()
        self.manager = DataSourceManager()
    
    def generate_signals(self, symbols: List[str]):
        """Generate signals based on value and quality metrics"""
        
        # Get fundamentals
        fundamentals = self.manager.fetch_fundamentals(symbols)
        
        signals = {}
        for symbol, data in fundamentals.items():
            pe = data.get('pe_ratio')
            pb = data.get('pb_ratio')
            roe = data.get('roe')
            
            # Value screen: P/E < 20
            # Quality screen: ROE > 15%
            if pe and pb and roe:
                if pe < 20 and roe > 0.15:
                    signals[symbol] = 'BUY'
                elif pe > 30 and roe < 0.05:
                    signals[symbol] = 'SELL'
        
        return signals
```

### Example: Dividend Growth Screen

```python
class DividendGrowthStrategy(SignalGenerator):
    def __init__(self):
        super().__init__()
        self.manager = DataSourceManager()
    
    def generate_signals(self, symbols: List[str]):
        """Generate signals for dividend growth stocks"""
        
        # Get corporate actions
        actions = self.manager.fetch_corporate_actions(symbols)
        
        # Get fundamentals
        fundamentals = self.manager.fetch_fundamentals(symbols)
        
        signals = {}
        for symbol in symbols:
            # Check dividend history
            dividend_actions = [a for a in actions.get(symbol, []) if a['type'] == 'dividend']
            fund = fundamentals.get(symbol, {})
            
            # If consistent dividends and growing, buy
            if len(dividend_actions) > 8:  # 2+ years of history
                if fund.get('dividend_yield', 0) > 0.02:  # 2%+ yield
                    signals[symbol] = 'BUY'
        
        return signals
```

## 3. Backtesting Integration

### Using OHLC Database for Backtesting

```python
from src.backtesting.backtest_engine import BacktestEngine

class DataSourceBacktest(BacktestEngine):
    def __init__(self, symbols: List[str]):
        super().__init__()
        self.ohlc = OHLCPipeline()
        self.symbols = symbols
    
    def run_backtest(self, start_date: datetime, end_date: datetime):
        """Run backtest using stored data"""
        
        backtest_data = {}
        
        # Get data for each symbol
        for symbol in self.symbols:
            df = self.ohlc.get_data(
                symbol, 
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if not df.empty:
                backtest_data[symbol] = df
        
        # Run backtest with this data
        return self.execute_backtest(backtest_data)
```

## 4. Real-time Strategy Integration

### Monitor Corporate Actions

```python
from datetime import datetime, timedelta

class CorporateActionMonitor:
    def __init__(self, watchlist: List[str]):
        self.manager = DataSourceManager()
        self.watchlist = watchlist
        self.last_check = datetime.now()
    
    def check_for_actions(self) -> Dict[str, List]:
        """Check for recent corporate actions"""
        
        # Get actions from last update
        start_date = self.last_check
        end_date = datetime.now()
        
        actions = self.manager.fetch_corporate_actions(
            self.watchlist,
            start_date=start_date,
            end_date=end_date
        )
        
        # Alert on splits (need position adjustment)
        for symbol, action_list in actions.items():
            for action in action_list:
                if action['type'] == 'split':
                    print(f"⚠ SPLIT ALERT: {symbol} split {action['ratio']}")
                    # Adjust positions accordingly
        
        self.last_check = end_date
        return actions
```

## 5. Feature Engineering with Data Sources

### Creating Technical Features

```python
import pandas as pd
from src.feature_store.features import FeatureStore

class DataSourceFeatures:
    def __init__(self):
        self.ohlc = OHLCPipeline()
        self.fundamentals_db = FundamentalsPipeline()
        self.store = FeatureStore()
    
    def create_features(self, symbol: str, date: str):
        """Create technical and fundamental features"""
        
        features = {}
        
        # Get recent OHLC data
        df = self.ohlc.get_latest(symbol, bars=100)
        
        # Technical features
        features['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
        features['sma_50'] = df['close'].rolling(50).mean().iloc[-1]
        features['volatility'] = df['close'].pct_change().std()
        features['momentum'] = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        
        # Fundamental features
        fund = self.fundamentals_db.get_fundamentals(symbol, date)
        features['pe_ratio'] = fund.get('pe_ratio', 0)
        features['pb_ratio'] = fund.get('pb_ratio', 0)
        features['roe'] = fund.get('roe', 0)
        features['dividend_yield'] = fund.get('dividend_yield', 0)
        
        # Store features
        self.store.add_feature_vector(symbol, date, features)
        
        return features
```

## 6. Risk Management Integration

### Corporate Action Adjustments

```python
from src.risk.risk_manager import RiskManager

class DataSourceRiskManager(RiskManager):
    def __init__(self):
        super().__init__()
        self.manager = DataSourceManager()
    
    def adjust_for_corporate_actions(self, symbol: str):
        """Adjust positions for splits and dividends"""
        
        # Get recent corporate actions
        actions = self.manager.fetch_corporate_actions([symbol])
        
        for action in actions.get(symbol, []):
            if action['type'] == 'split':
                # Adjust position and stop loss levels
                split_ratio = action['ratio']
                self.adjust_position_for_split(symbol, split_ratio)
            
            elif action['type'] == 'dividend':
                # Adjust for expected dividend income
                dividend_amount = action['amount']
                self.adjust_for_dividend(symbol, dividend_amount)
```

## 7. Portfolio Optimization with Fundamentals

### Optimization with Factor Constraints

```python
import numpy as np
from scipy.optimize import minimize

class FundamentalOptimizer:
    def __init__(self):
        self.manager = DataSourceManager()
    
    def optimize_portfolio(self, symbols: List[str], target_return: float):
        """Optimize portfolio with fundamental constraints"""
        
        # Get fundamentals and prices
        fundamentals = self.manager.fetch_fundamentals(symbols)
        prices = self.manager.fetch_price_data(symbols, 
                                               datetime.now() - timedelta(days=365),
                                               datetime.now())
        
        # Extract quality scores
        quality_scores = {}
        for symbol, data in fundamentals.items():
            # Composite score: (ROE + (1/P/E)) / 2
            roe = data.get('roe', 0) * 100
            pe = data.get('pe_ratio', 1)
            pe_score = 100 / pe if pe > 0 else 0
            quality_scores[symbol] = (roe + pe_score) / 2
        
        # Optimize with quality constraints
        def constraint_quality(weights):
            quality_weighted = sum(weights[i] * quality_scores[s] 
                                   for i, s in enumerate(symbols))
            return quality_weighted - 50  # Minimum quality threshold
        
        # Run optimization...
        return self.run_optimization(symbols, constraint_quality)
```

## 8. Macro-Aware Strategy

### Use Macro Data for Context

```python
class MacroAwareStrategy(SignalGenerator):
    def __init__(self):
        super().__init__()
        self.manager = DataSourceManager()
    
    def generate_signals_with_macro(self, symbols: List[str]):
        """Generate signals adjusted for macro conditions"""
        
        # Get macro conditions
        start = datetime.now() - timedelta(days=365*10)
        end = datetime.now()
        macro = self.manager.fetch_macro_data(['GDP', 'UNRATE'], start, end)
        
        # Assess macro regime
        gdp_growth = macro['GDP']['value'].pct_change().mean() if 'GDP' in macro else 0
        unemployment = macro['UNRATE']['value'].iloc[-1] if 'UNRATE' in macro else 5
        
        # Adjust strategy based on macro
        if unemployment > 6 and gdp_growth < 0:
            # Recession: favor defensive stocks
            return self.generate_defensive_signals(symbols)
        else:
            # Growth: favor growth stocks
            return self.generate_growth_signals(symbols)
```

## 9. Data Pipeline Integration

### Scheduled Data Updates

```python
from apscheduler.schedulers.background import BackgroundScheduler

class ScheduledDataUpdate:
    def __init__(self):
        self.manager = DataSourceManager()
        self.ohlc = OHLCPipeline()
        self.fundamentals_db = FundamentalsPipeline()
        self.scheduler = BackgroundScheduler()
    
    def start_updates(self, symbols: List[str]):
        """Start scheduled data updates"""
        
        # Update OHLC daily
        self.scheduler.add_job(
            self.update_ohlc,
            'cron',
            hour=16,  # After market close
            args=[symbols]
        )
        
        # Update fundamentals weekly
        self.scheduler.add_job(
            self.update_fundamentals,
            'cron',
            day_of_week='fri',
            hour=17,
            args=[symbols]
        )
        
        self.scheduler.start()
    
    def update_ohlc(self, symbols: List[str]):
        """Update OHLC data"""
        end = datetime.now()
        start = end - timedelta(days=365)
        
        prices = self.manager.fetch_price_data(symbols, start, end)
        print(f"Updated OHLC for {len(symbols)} symbols")
    
    def update_fundamentals(self, symbols: List[str]):
        """Update fundamentals"""
        fundamentals = self.manager.fetch_fundamentals(symbols)
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        for symbol, data in fundamentals.items():
            self.fundamentals_db.store_fundamentals(symbol, date_str, data)
        
        print(f"Updated fundamentals for {len(fundamentals)} symbols")
```

## 10. Monitoring and Alerts

### Data Quality Monitoring

```python
class DataQualityMonitor:
    def __init__(self):
        self.manager = DataSourceManager()
        self.ohlc = OHLCPipeline()
    
    def check_data_quality(self, symbols: List[str]):
        """Monitor data quality and alert on issues"""
        
        alerts = []
        
        for symbol in symbols:
            # Get latest data
            df = self.ohlc.get_latest(symbol, bars=5)
            
            if df.empty:
                alerts.append(f"⚠ {symbol}: No data available")
                continue
            
            # Check for stale data
            last_date = pd.to_datetime(df['date'].iloc[-1])
            days_old = (datetime.now() - last_date).days
            
            if days_old > 3:
                alerts.append(f"⚠ {symbol}: Data is {days_old} days old")
            
            # Check for unusual prices
            latest_close = df['close'].iloc[-1]
            avg_close = df['close'].mean()
            pct_change = abs(latest_close - avg_close) / avg_close
            
            if pct_change > 0.2:
                alerts.append(f"⚠ {symbol}: Price moved {pct_change*100:.1f}%")
        
        return alerts
```

## Best Practices

### 1. Cache Management
```python
# Enable cache for production
manager = DataSourceManager(cache_enabled=True)

# Disable for real-time testing
manager = DataSourceManager(cache_enabled=False)
```

### 2. Error Handling
```python
try:
    prices = manager.fetch_price_data(symbols, start, end)
    if prices.empty:
        # Use cached data or previous day's data
        prices = self.ohlc.get_latest(symbols[0], bars=100)
except Exception as e:
    logger.error(f"Error fetching prices: {e}")
    # Fall back to database
    prices = self.ohlc.get_data(symbols[0])
```

### 3. Performance
```python
# Batch requests
symbols = ['AAPL', 'MSFT', 'GOOGL', ...]  # 100+ symbols
prices = manager.fetch_price_data(symbols, start, end)

# Use database for historical data
df = self.ohlc.get_data(symbol, start_date, end_date)

# Cache frequently-used data
fundamentals = manager.fetch_fundamentals(symbols)  # Cached for 7 days
```

### 4. Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Fetching data for {len(symbols)} symbols")
logger.debug(f"Using source: {source.name}")
logger.warning(f"Source {source.name} failed, trying fallback")
```

## Testing Integration

```python
import unittest

class TestDataSourceIntegration(unittest.TestCase):
    def setUp(self):
        self.manager = DataSourceManager()
        self.ohlc = OHLCPipeline()
    
    def test_fetch_price_data(self):
        """Test price data fetching"""
        prices = self.manager.fetch_price_data(['AAPL'], 
                                               datetime(2024, 1, 1),
                                               datetime(2024, 1, 31))
        self.assertFalse(prices.empty)
        self.assertIn('close', prices.columns)
    
    def test_fetch_fundamentals(self):
        """Test fundamentals fetching"""
        fund = self.manager.fetch_fundamentals(['AAPL'])
        self.assertIn('AAPL', fund)
        self.assertIn('pe_ratio', fund['AAPL'])
    
    def test_database_storage(self):
        """Test database operations"""
        self.ohlc.fetch_and_store(['AAPL'], period='1mo')
        df = self.ohlc.get_data('AAPL')
        self.assertFalse(df.empty)
```

## Summary

The data sources system integrates seamlessly with:
- ✅ Signal generation and validation
- ✅ Backtesting engine
- ✅ Risk management
- ✅ Portfolio optimization
- ✅ Feature engineering
- ✅ Monitoring and alerts
- ✅ Scheduled updates

For detailed information on each component, see:
- **DATA_SOURCES_CONFIGURATION.md** - Complete reference
- **DATA_SOURCES_QUICKSTART.md** - Quick setup
- **src/data/** - Source code and examples
