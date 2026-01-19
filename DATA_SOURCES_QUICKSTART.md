# Data Sources Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Set Environment Variables
Choose the data sources you want to use and set their API keys:

```bash
# Option 1: Yahoo Finance (No API Key - RECOMMENDED FOR START)
# No setup needed! Yahoo Finance works without credentials

# Option 2: Add Financial Modeling Prep (FMP)
export FMP_API_KEY="your_fmp_api_key"

# Option 3: Add FRED (Federal Reserve Data)
export FRED_API_KEY="your_fred_api_key"

# Option 4: Add Alpha Vantage
export ALPHA_VANTAGE_KEY="your_alpha_vantage_key"

# Option 5: Add Quandl
export QUANDL_API_KEY="your_quandl_api_key"
```

### Step 2: Verify Configuration

```bash
# Quick validation (no data fetch)
python validate_data_sources.py

# Should show:
#   ✓ Yahoo Finance: OK
#   ✓ Fundamentals available
#   ✓ Cache system ready
```

### Step 3: Setup Databases and Fetch Initial Data

```bash
# Quick setup (databases only)
python setup_data_sources.py --quick

# Full setup (databases + initial data)
python setup_data_sources.py --full

# Custom symbols
python setup_data_sources.py --symbols AAPL,MSFT,GOOGL --days 90
```

### Step 4: Use in Your Code

```python
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()

# Fetch price data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
prices = manager.fetch_price_data(['AAPL', 'MSFT'], start_date, end_date)

# Fetch fundamentals
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT'])

# Fetch corporate actions
actions = manager.fetch_corporate_actions(['AAPL'])

print(prices.head())
print(fundamentals)
```

## ✨ What You Get Out of the Box

### 1. **Price Data** ✓
- Yahoo Finance (no setup required)
- Daily, hourly, or minute data
- Automatic caching (1-day TTL)
- Fallback support

```python
# Get last 30 days of AAPL
prices = manager.fetch_price_data(['AAPL'], 
                                 start_date=datetime(2024,1,1),
                                 end_date=datetime(2024,12,31))
```

### 2. **Fundamentals** ✓
- P/E Ratio, P/B Ratio
- ROE, ROA, Debt/Equity
- Market Cap, Dividend Yield
- 7-day cache

```python
# Get latest fundamentals
fund = manager.fetch_fundamentals(['AAPL'])
print(f"P/E: {fund['AAPL']['pe_ratio']}")
```

### 3. **Corporate Actions** ✓
- Dividends with amounts
- Stock splits with ratios
- Historical tracking
- 30-day cache

```python
# Get all dividends and splits
actions = manager.fetch_corporate_actions(['JNJ', 'KO'])
```

### 4. **Macro Data** 📊 (Optional - FRED)
- GDP, Unemployment, CPI
- 500,000+ economic indicators
- 7-day cache

```python
# Get GDP data (requires FRED_API_KEY)
macro = manager.fetch_macro_data(['GDP'], start_date, end_date)
```

## 📁 Project Structure

```
Trading_Bot01/
├── data/                          # Data storage
│   ├── ohlc_data.db              # Price data database
│   ├── fundamentals_data.db      # Fundamentals database
│   └── .cache/                   # Cached API responses
├── src/data/                      # Data source code
│   ├── data_source_manager.py    # Main manager (fetch from any source)
│   ├── data_sources_config.py    # Configuration definitions
│   ├── ohlc_pipeline.py          # Price data storage
│   ├── fundamentals_pipeline.py  # Fundamentals storage
│   └── multi_source_pipeline.py  # Direct source connectors
├── setup_data_sources.py          # Setup script
├── validate_data_sources.py       # Validation script
└── DATA_SOURCES_CONFIGURATION.md  # Detailed guide
```

## 🔌 Data Source Priorities

The system automatically tries sources in this order:

### Price Data
1. Yahoo Finance ✓ (always works)
2. FMP (if API key set)
3. Alpha Vantage (if API key set)

### Fundamentals
1. FMP (if API key set)
2. Yahoo Finance ✓ (always works)

### Corporate Actions
1. Yahoo Finance ✓ (always works)
2. FMP (if API key set)

### Macro Data
1. FRED (if API key set)
2. World Bank ✓ (always works)
3. Quandl (if API key set)

## 📊 Database Access

### Store and Retrieve Price Data

```python
from src.data.ohlc_pipeline import OHLCPipeline

ohlc = OHLCPipeline()

# Store data from Yahoo
ohlc.fetch_and_store(['AAPL', 'MSFT'], period='1y', interval='1d')

# Retrieve data
df = ohlc.get_data('AAPL', start_date='2024-01-01', end_date='2024-12-31')

# Get latest N bars
latest = ohlc.get_latest('AAPL', bars=100)

# See all symbols in database
symbols = ohlc.get_symbols()
```

### Store and Retrieve Fundamentals

```python
from src.data.fundamentals_pipeline import FundamentalsPipeline

fund_db = FundamentalsPipeline()

# Store fundamentals
fund_db.store_fundamentals('AAPL', '2024-01-31', {
    'pe_ratio': 25.5,
    'pb_ratio': 42.1,
    'debt_to_equity': 1.23,
    'roe': 0.85,
    'roa': 0.28,
    'dividend_yield': 0.004,
    'market_cap': 3000000000000
})

# Retrieve
data = fund_db.get_fundamentals('AAPL', date='2024-01-31')
```

## 💾 Caching System

Data is automatically cached to reduce API calls:

```
data/.cache/                  # Cache directory
├── *.pkl                     # Cached responses
```

Cache settings:
- **Price Data**: 1 day (updated daily)
- **Fundamentals**: 7 days (quarterly)
- **Corporate Actions**: 30 days (rare changes)
- **Macro Data**: 7 days

**Disable cache** (not recommended):
```python
manager = DataSourceManager(cache_enabled=False)
```

## 🧪 Test Your Setup

### Run Examples
```bash
# Run all example workflows
python examples_data_sources.py --all

# Run specific example
python examples_data_sources.py --example 1

# Available examples:
# 1: Fetch Price Data
# 2: Store and Retrieve OHLC
# 3: Fetch Fundamentals
# 4: Fetch Corporate Actions
# 5: Fetch Macro Data
# 6: FMP Connector (requires API key)
# 7: Yahoo Connector
# 8: Complete Workflow
```

### Validate Configuration
```bash
python validate_data_sources.py

# Output shows:
# - Configured API keys
# - Data sources status
# - Directory structure
# - Database files
# - Connectivity tests
```

## 🛠️ Common Tasks

### Get Latest Stock Price
```python
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()
end = datetime.now()
start = end - timedelta(days=1)

prices = manager.fetch_price_data(['AAPL'], start, end)
latest_price = prices['close'].iloc[-1]
print(f"AAPL: ${latest_price:.2f}")
```

### Get Company P/E Ratio
```python
manager = DataSourceManager()
fundamentals = manager.fetch_fundamentals(['AAPL'])
pe_ratio = fundamentals['AAPL'].get('pe_ratio')
print(f"P/E Ratio: {pe_ratio:.2f}")
```

### Track Dividend History
```python
manager = DataSourceManager()
actions = manager.fetch_corporate_actions(['JNJ'])

print("JNJ Dividends:")
for action in actions['JNJ']:
    if action['type'] == 'dividend':
        print(f"  {action['date']}: ${action['amount']:.2f}")
```

### Build Historical Dataset
```python
from src.data.ohlc_pipeline import OHLCPipeline
import pandas as pd

ohlc = OHLCPipeline()

# Store 1 year of data
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
ohlc.fetch_and_store(symbols, period='1y', interval='1d')

# Retrieve all data
for symbol in symbols:
    df = ohlc.get_data(symbol)
    print(f"{symbol}: {len(df)} rows")
```

### Compare Multiple Strategies
```python
manager = DataSourceManager()

# Get prices
prices = manager.fetch_price_data(symbols, start, end)

# Get fundamentals for screening
fundamentals = manager.fetch_fundamentals(symbols)

# Get corporate actions for adjustments
actions = manager.fetch_corporate_actions(symbols)

# Combine for analysis
print(f"Symbols with P/E < 20:")
for symbol, fund in fundamentals.items():
    if fund.get('pe_ratio') and fund['pe_ratio'] < 20:
        print(f"  {symbol}: {fund['pe_ratio']:.2f}")
```

## 🎓 Learning Resources

### Documentation
- **Detailed Config**: See [DATA_SOURCES_CONFIGURATION.md](DATA_SOURCES_CONFIGURATION.md)
- **API Examples**: See [examples_data_sources.py](examples_data_sources.py)
- **Source Code**: See `src/data/` directory

### External Resources
- **Yahoo Finance**: https://finance.yahoo.com
- **FMP Docs**: https://financialmodelingprep.com/developer/docs
- **FRED Docs**: https://fred.stlouisfed.org/docs/api
- **Alpha Vantage Docs**: https://www.alphavantage.co/documentation

## 🚨 Troubleshooting

### Issue: "No API Key" warnings
```
WARNING: FMP_API_KEY not set. FMP features will be limited.
```
**Solution**: 
- Set `FMP_API_KEY` environment variable, OR
- Use Yahoo Finance (works without API key)

### Issue: Rate limit exceeded
```
ERROR: 429 Too Many Requests
```
**Solution**:
- Cache is enabled by default (1-day for prices)
- Wait before retrying
- Upgrade to paid API tier

### Issue: Empty data returned
```
WARNING: All price data sources failed
```
**Solution**:
- Check internet connection
- Verify symbol exists (e.g., `AAPL` not `APPLE`)
- Check API key validity
- See `logs/data_sources_setup.log`

### Issue: "Database locked"
```
ERROR: database is locked
```
**Solution**:
- Close other processes using the database
- Restart Python interpreter
- Check for incomplete transactions

## ✅ Checklist

After setup, verify:

- [ ] Environment variables set (if using optional APIs)
- [ ] `python validate_data_sources.py` passes
- [ ] `python setup_data_sources.py --quick` completes
- [ ] `data/ohlc_data.db` exists
- [ ] `data/fundamentals_data.db` exists
- [ ] `python examples_data_sources.py` runs examples
- [ ] Can fetch data in Python:
  ```python
  from src.data.data_source_manager import DataSourceManager
  from datetime import datetime, timedelta
  
  m = DataSourceManager()
  data = m.fetch_price_data(['AAPL'], datetime.now()-timedelta(30), datetime.now())
  assert not data.empty, "No data retrieved!"
  print("✓ Data sources working!")
  ```

## 🎯 Next Steps

1. **Explore your data**: Run examples and see what's available
2. **Build your pipeline**: Use data sources in your trading strategy
3. **Optimize**: Cache frequently-used data, schedule updates
4. **Scale**: Use API keys to unlock more data sources
5. **Monitor**: Check `logs/` for issues and performance

## 📞 Support

For issues or questions:

1. Check **DATA_SOURCES_CONFIGURATION.md** for detailed docs
2. Run `validate_data_sources.py` to diagnose
3. Review logs: `logs/data_sources_*.log`
4. See examples: `examples_data_sources.py --all`

---

**Happy Trading! 📈**
