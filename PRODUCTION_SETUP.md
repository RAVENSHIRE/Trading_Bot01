# Production Trading System - Hedge Fund Setup

## Overview

Your Trading_Bot01 has been upgraded to **Production-Grade Hedge Fund Infrastructure**. This guide covers all new components.

---

## Architecture

```
Trading_Bot01/
├── database/
│   ├── cache/              # Cached features & data
│   ├── fmp/                # Financial Modeling Prep data (Parquet)
│   ├── yahoo/              # Yahoo Finance cache
│   ├── user/               # Custom user data
│   ├── optuna/             # Optimization trials
│   └── qsconnect.duckdb    # Analytics database
├── src/
│   ├── analytics/          # DuckDB analytics engine
│   ├── feature_store/      # Feature engineering & caching
│   ├── optimization/       # Optuna hyperparameter tuning
│   └── [existing modules]
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── orchestration/
│   └── prefect_flows.py    # Workflow automation
└── [existing structure]
```

---

## Component Guide

### 1. **Multi-Source Data Pipeline** (`src/data/multi_source_pipeline.py`)

Integrates multiple data sources:

#### Features:
- **Yahoo Finance**: Market data (OHLCV) with caching
- **FMP (Financial Modeling Prep)**: Bulk ratios, company profiles, income statements
- **Data Versioning**: Automatic date-stamping of cached data
- **Error Handling**: Graceful fallbacks when APIs fail

#### Usage:

```python
from data.multi_source_pipeline import MultiSourcePipeline
from datetime import datetime, timedelta

pipeline = MultiSourcePipeline()

# Fetch market data
symbols = ['AAPL', 'MSFT', 'GOOGL']
end = datetime.now()
start = end - timedelta(days=365)

market_data, fundamentals, ratios = pipeline.merge_all_sources(symbols, start, end)

print(market_data.head())
print(fundamentals.head())
```

#### Environment Variables:
```bash
FMP_API_KEY=your_api_key_here
```

---

### 2. **DuckDB Analytics Layer** (`src/analytics/duckdb_analytics.py`)

High-performance analytical queries:

#### Key Capabilities:
- **Momentum Screening**: Find stocks with positive returns
- **Value Screening**: Filter by P/E ratio and fundamentals
- **Correlation Analysis**: Multi-stock correlation matrices
- **Portfolio Stats**: Sharpe ratio, max drawdown, win rate
- **Performance Tracking**: Stock performance over time windows

#### Usage:

```python
from analytics.duckdb_analytics import DuckDBAnalytics

with DuckDBAnalytics() as db:
    # Insert market data
    db.insert_market_data(market_data_df)
    
    # Run analytics queries
    momentum_stocks = db.get_momentum_screen(min_return=0.05, days=60)
    value_stocks = db.get_value_screen(max_pe=15.0)
    
    # Calculate correlations
    corr_matrix = db.get_correlation_matrix(['AAPL', 'MSFT', 'GOOGL'], days=252)
    
    # Get portfolio statistics
    stats = db.get_portfolio_stats(trades_df)
```

#### Tables Created:
- `market_data`: OHLCV historical data
- `fundamentals`: Company metrics
- `financial_ratios`: P/E, P/B, ROE, ROA, etc.
- `signals`: Generated trading signals
- `trades`: Executed trades with P&L

---

### 3. **Optuna Hyperparameter Optimization** (`src/optimization/optuna_tuner.py`)

Automated parameter tuning for trading signals:

#### Supported Signals:
- **Momentum**: Fast MA, Slow MA, RSI parameters
- **Mean Reversion**: Lookback, Z-score threshold, ATR
- **Custom**: User-defined objective functions

#### Usage:

```python
from optimization.optuna_tuner import ParameterTuner

tuner = ParameterTuner()

# Optimize momentum signal
best_params = tuner.tune_signal_parameters(
    signal_type="momentum",
    price_data=market_data_df,
    n_trials=100
)

print(f"Best parameters: {best_params}")
print(f"Best Sharpe ratio: {best_params['best_sharpe']}")
```

#### Results:
- Studies stored in SQLite (database/optuna/optuna.db)
- Access optimization history: `optimizer.get_study_results('study_name')`
- Export to CSV: `optimizer.export_results('study_name', 'output.csv')`

---

### 4. **Feature Store** (`src/feature_store/features.py`)

Centralized feature management:

#### Technical Features:
- **Moving Averages**: SMA, EMA
- **Momentum**: RSI, MACD, ROC
- **Volatility**: Bollinger Bands, ATR
- **Volume**: Volume MA, Volume Ratio, Z-scores

#### Fundamental Features:
- **Value Metrics**: P/E inverse, P/B inverse, Leverage
- **Growth Metrics**: Revenue, earnings, dividend growth
- **Profitability**: ROE, ROA, margins

#### Usage:

```python
from feature_store.features import FeatureEngineering

fe = FeatureEngineering()

# Generate technical features
features = fe.create_price_features(ohlcv_df)

# Get fundamental features
fund_features = fe.create_fundamental_features({
    'pe_ratio': 15.5,
    'roe': 0.18,
    'debt_equity': 0.5
})

# Cache all features
fe.cache_all_features()
```

---

### 5. **Streamlit Dashboard** (`dashboard/app.py`)

Real-time monitoring interface:

#### Pages:
1. **Portfolio**: Metrics, positions, P&L
2. **Data Sources**: Fetch and preview market/fundamental data
3. **Features**: Technical and fundamental feature generation
4. **Optimization**: Hyperparameter tuning interface
5. **Settings**: Configuration options

#### Running the Dashboard:

```bash
streamlit run dashboard/app.py
```

Access at: `http://localhost:8501`

#### Features:
- Real-time portfolio metrics
- Data source management
- Technical analysis feature generation
- Signal optimization visualization

---

### 6. **Prefect Orchestration** (`orchestration/prefect_flows.py`)

Automated workflow scheduling:

#### Available Flows:
1. **nightly-data-pipeline**: Daily data refresh (10 symbols)
2. **nightly-signal-optimization**: Daily parameter tuning
3. **hourly-market-check**: Hourly momentum screening

#### Usage without Prefect:

```python
from orchestration.prefect_flows import nightly_data_pipeline

# Run manually
result = nightly_data_pipeline()
```

#### With Prefect (Optional):

```bash
pip install prefect
prefect serve orchestration/prefect_flows.py
```

---

## Data Flow

```
Yahoo Finance / FMP APIs
         ↓
MultiSourcePipeline (fetch & cache)
         ↓
DuckDB (store & analyze)
         ↓
FeatureStore (engineer features)
         ↓
Optuna (optimize parameters)
         ↓
Dashboard (visualize)
         ↓
Trading Signals → Execution
```

---

## Database Schema

### market_data table
```sql
CREATE TABLE market_data (
    date DATE,
    symbol VARCHAR,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume INTEGER,
    adj_close FLOAT
);
```

### fundamentals table
```sql
CREATE TABLE fundamentals (
    symbol VARCHAR PRIMARY KEY,
    market_cap BIGINT,
    pe_ratio FLOAT,
    dividend_yield FLOAT,
    fifty_two_week_high FLOAT,
    fifty_two_week_low FLOAT,
    beta FLOAT,
    book_value FLOAT,
    updated_date DATE
);
```

---

## Configuration

### Environment Variables

```bash
# Financial data
FMP_API_KEY=your_key_here

# Database
DUCKDB_PATH=/workspaces/Trading_Bot01/database/qsconnect.duckdb

# Feature Store
FEATURE_CACHE_DIR=/workspaces/Trading_Bot01/database/cache

# Optimization
OPTUNA_DB_PATH=sqlite:////workspaces/Trading_Bot01/database/optuna/optuna.db
```

Create `.env` file in project root:
```
FMP_API_KEY=your_api_key
```

---

## Performance Considerations

### DuckDB
- Columnar storage for analytical queries
- Automatic indexing on commonly queried columns
- In-process, no network overhead

### Feature Store
- Parquet format for compression (50-70% reduction)
- Lazy loading to reduce memory footprint
- TTL-based cache invalidation

### Optuna
- TPE sampler for efficient exploration
- Median pruner to stop unpromising trials early
- Parallel trial execution support

---

## Integration with Existing Modules

### Signal Generation
```python
from signals.signal_generator import SignalGenerator
from feature_store.features import FeatureEngineering

fe = FeatureEngineering()
features = fe.create_price_features(ohlcv_data)

sg = SignalGenerator(ohlcv_data)
signals = sg.momentum_signal(fast_period=12, slow_period=26)
```

### Portfolio Management
```python
from core.portfolio import Portfolio
from analytics.duckdb_analytics import DuckDBAnalytics

portfolio = Portfolio(initial_capital=100000)
analytics = DuckDBAnalytics()

# Store trades in analytics
analytics.get_portfolio_stats(portfolio.get_trades_df())
```

### Risk Management
```python
from risk.risk_manager import RiskManager
from analytics.duckdb_analytics import DuckDBAnalytics

risk_mgr = RiskManager()
analytics = DuckDBAnalytics()

# Validate position against risk limits
momentum_stocks = analytics.get_momentum_screen()
```

---

## Next Steps

1. **Set FMP API Key**: Get from https://financialmodelingprep.com
2. **Install Prefect** (optional): `pip install prefect`
3. **Run Dashboard**: `streamlit run dashboard/app.py`
4. **Start Data Pipeline**: `python orchestration/prefect_flows.py`
5. **Optimize Signals**: Use dashboard or direct API

---

## Troubleshooting

### DuckDB connection errors
- Check database path permissions
- Ensure database directory exists: `mkdir -p database`

### FMP API rate limiting
- Data is cached to disk automatically
- Reduce query frequency or upgrade FMP plan

### Feature generation memory issues
- Use `cache_all_features()` to move to disk
- Process symbols in batches

### Optuna trials not improving
- Increase `n_trials` for longer search
- Adjust parameter ranges in objective function
- Use different signal type

---

## Architecture Highlights

✅ **Modular Design**: Each component is independent  
✅ **Production-Ready**: Error handling, logging, monitoring  
✅ **Scalable**: Parquet, DuckDB, Optuna support parallelization  
✅ **Data-Driven**: Feature store + optimization for better signals  
✅ **Observable**: Dashboard for real-time monitoring  
✅ **Reproducible**: Versioned data, logged parameters, stored results  

---

For more details, see individual module docstrings.
