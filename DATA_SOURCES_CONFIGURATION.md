# Data Sources Configuration Guide

## Overview

The Trading Bot supports multiple data sources for price data, fundamentals, corporate actions, and macro data. This guide explains how to configure and use each data source.

## Supported Data Sources

### Price Data Sources

#### 1. Yahoo Finance ✓ (No API Key Required)
- **Status**: Always enabled
- **Rate Limit**: 2,000 requests/minute
- **Features**: OHLCV data, dividends, splits
- **Cache TTL**: 1 day
- **Best For**: General price data, highly reliable

```python
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

price_data = manager.fetch_price_data(
    symbols=['AAPL', 'MSFT'],
    start_date=start_date,
    end_date=end_date,
    interval='1d'
)
```

#### 2. Financial Modeling Prep (FMP) 📊
- **Status**: Conditional (requires API key)
- **API Key**: `FMP_API_KEY` environment variable
- **Rate Limit**: 300 requests/minute
- **Website**: https://financialmodelingprep.com
- **Features**: Historical prices, fundamentals, financials, ratios
- **Free Tier**: Limited API calls
- **Cache TTL**: 1 day (prices), 7 days (fundamentals)

**Setup**:
```bash
export FMP_API_KEY="your_api_key_here"
```

**Usage**:
```python
from src.data.multi_source_pipeline import FMPConnector

fmp = FMPConnector()

# Fetch company profile
profile = fmp.get_company_profile('AAPL')

# Fetch bulk ratios
ratios = fmp.get_bulk_ratios(period='quarter')

# Fetch income statement
income = fmp.get_income_statement('AAPL', period='quarter', limit=10)
```

#### 3. Alpha Vantage 📈
- **Status**: Conditional (requires API key)
- **API Key**: `ALPHA_VANTAGE_KEY` environment variable
- **Rate Limit**: 5 requests/minute (free tier)
- **Website**: https://www.alphavantage.co
- **Features**: Intraday, daily, weekly, monthly OHLCV
- **Best For**: Technical data with different intervals
- **Cache TTL**: 1 day

**Setup**:
```bash
export ALPHA_VANTAGE_KEY="your_api_key_here"
```

### Fundamentals Data Sources

#### 1. Yahoo Finance ✓ (No API Key Required)
- **Status**: Always enabled
- **Features**: P/E ratio, P/B ratio, ROE, ROA, market cap, dividend yield
- **Cache TTL**: 7 days

#### 2. Financial Modeling Prep (FMP) 📊
- **Status**: Conditional (requires API key)
- **Features**: Comprehensive financial metrics, ratios, growth metrics
- **Cache TTL**: 7 days

**Example**:
```python
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT'])

# Returns:
# {
#     'AAPL': {
#         'pe_ratio': 25.5,
#         'pb_ratio': 42.1,
#         'debt_to_equity': 1.23,
#         'roe': 0.85,
#         'roa': 0.28,
#         'dividend_yield': 0.004,
#         'market_cap': 3000000000000
#     }
# }
```

### Corporate Actions Sources

#### 1. Yahoo Finance ✓ (No API Key Required)
- **Status**: Always enabled
- **Features**: Dividends, stock splits
- **Cache TTL**: 30 days

#### 2. Financial Modeling Prep (FMP) 📊
- **Status**: Conditional (requires API key)
- **Features**: Dividends, splits with detailed information
- **Cache TTL**: 30 days

**Example**:
```python
actions = manager.fetch_corporate_actions(['AAPL'], 
                                         start_date=datetime(2020, 1, 1))

# Returns:
# {
#     'AAPL': [
#         {'type': 'dividend', 'date': '2024-05-17', 'amount': 0.24},
#         {'type': 'split', 'date': '2020-08-31', 'ratio': 4.0}
#     ]
# }
```

### Macro Data Sources

#### 1. FRED (Federal Reserve Economic Data) 📉
- **Status**: Conditional (requires API key)
- **API Key**: `FRED_API_KEY` environment variable
- **Website**: https://fred.stlouisfed.org
- **Rate Limit**: 120 requests/minute
- **Features**: 500,000+ US economic time series
- **Cache TTL**: 7 days

**Setup**:
```bash
export FRED_API_KEY="your_api_key_here"
```

**Common Indicators**:
- `GDP`: Real Gross Domestic Product
- `UNRATE`: Unemployment Rate
- `CPIAUCSL`: Consumer Price Index
- `PAYEMS`: Total Nonfarm Payroll

#### 2. World Bank Open Data ✓ (No API Key Required)
- **Status**: Always enabled
- **Website**: https://data.worldbank.org
- **Rate Limit**: 600 requests/minute
- **Features**: Global development indicators
- **Cache TTL**: 30 days

#### 3. Quandl 📊
- **Status**: Conditional (requires API key)
- **API Key**: `QUANDL_API_KEY` environment variable
- **Website**: https://www.quandl.com
- **Features**: Alternative data, commodities, etc.
- **Cache TTL**: 7 days

**Setup**:
```bash
export QUANDL_API_KEY="your_api_key_here"
```

**Example**:
```python
macro_data = manager.fetch_macro_data(
    indicators=['GDP', 'UNRATE'],
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

## Configuration Files

### trading_config.ini

Main configuration file with API keys and data source settings:

```ini
[default]
# API Keys (use environment variables in production)
FMP_API_KEY=${FMP_API_KEY}
FRED_API_KEY=${FRED_API_KEY}
ALPHA_VANTAGE_KEY=${ALPHA_VANTAGE_KEY}
QUANDL_API_KEY=${QUANDL_API_KEY}

# Data Sources Configuration
PRICE_DATA_SOURCE=yahoo
FUNDAMENTALS_SOURCE=fmp
CORPORATE_ACTIONS_SOURCE=yahoo
MACRO_DATA_SOURCE=fred

# Cache Settings
CACHE_ENABLED=true
CACHE_DIR=data/.cache
PRICE_DATA_CACHE_TTL_DAYS=1
FUNDAMENTALS_CACHE_TTL_DAYS=7
CORPORATE_ACTIONS_CACHE_TTL_DAYS=30
MACRO_DATA_CACHE_TTL_DAYS=7
```

### data_sources_config.py

Python configuration module defining all data sources:

```python
from src.data.data_sources_config import DataSourcesConfig, DataSourceType

# Get enabled sources for a type
sources = DataSourcesConfig.get_sources_by_type(DataSourceType.PRICE_DATA)

# Get primary source
primary = DataSourcesConfig.get_primary_source(DataSourceType.FUNDAMENTALS)

# Validate API keys
validation = DataSourcesConfig.validate_api_keys()

# Get configuration summary
summary = DataSourcesConfig.get_configuration_summary()
print(summary)
```

## Environment Setup

### Setting Environment Variables

**Linux/macOS**:
```bash
export FMP_API_KEY="your_key"
export FRED_API_KEY="your_key"
export ALPHA_VANTAGE_KEY="your_key"
export QUANDL_API_KEY="your_key"
```

**Windows (PowerShell)**:
```powershell
$env:FMP_API_KEY="your_key"
$env:FRED_API_KEY="your_key"
```

**Windows (Command Prompt)**:
```cmd
set FMP_API_KEY=your_key
set FRED_API_KEY=your_key
```

**Using .env file** (with python-dotenv):
```bash
# .env
FMP_API_KEY=your_key
FRED_API_KEY=your_key
ALPHA_VANTAGE_KEY=your_key
QUANDL_API_KEY=your_key
```

Then load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Running Setup

### Quick Setup (No Data Fetch)
```bash
python setup_data_sources.py --quick
```

### Full Setup with Data Fetch
```bash
python setup_data_sources.py --full
```

### Custom Symbols and Period
```bash
python setup_data_sources.py --symbols AAPL,MSFT,GOOGL --days 90
```

### Skip Tests
```bash
python setup_data_sources.py --no-test
```

## Database Structure

### OHLC Database (`data/ohlc_data.db`)

```sql
CREATE TABLE ohlc (
    symbol TEXT,
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    adjusted_close REAL,
    PRIMARY KEY (symbol, date)
);
```

**Usage**:
```python
from src.data.ohlc_pipeline import OHLCPipeline

ohlc = OHLCPipeline()

# Fetch and store
ohlc.fetch_and_store(['AAPL', 'MSFT'], period='1y', interval='1d')

# Retrieve data
df = ohlc.get_data('AAPL', start_date='2024-01-01', end_date='2024-12-31')

# Get latest bars
latest = ohlc.get_latest('AAPL', bars=100)

# Get all symbols
symbols = ohlc.get_symbols()
```

### Fundamentals Database (`data/fundamentals_data.db`)

```sql
CREATE TABLE fundamentals (
    symbol TEXT,
    date TEXT,
    pe_ratio REAL,
    pb_ratio REAL,
    debt_to_equity REAL,
    roe REAL,
    roa REAL,
    dividend_yield REAL,
    market_cap REAL,
    PRIMARY KEY (symbol, date)
);
```

**Usage**:
```python
from src.data.fundamentals_pipeline import FundamentalsPipeline

fundamentals = FundamentalsPipeline()

# Store fundamentals
fundamentals.store_fundamentals('AAPL', '2024-01-31', {
    'pe_ratio': 25.5,
    'pb_ratio': 42.1,
    'debt_to_equity': 1.23,
    'roe': 0.85,
    'roa': 0.28,
    'dividend_yield': 0.004,
    'market_cap': 3000000000000
})

# Retrieve
fund = fundamentals.get_fundamentals('AAPL', date='2024-01-31')
```

## Caching System

The bot includes an intelligent caching system to reduce API calls:

- **Price Data**: 1-day cache (updated daily)
- **Fundamentals**: 7-day cache (quarterly updates)
- **Corporate Actions**: 30-day cache (infrequent changes)
- **Macro Data**: 7-day cache

**Cache Location**: `data/.cache/`

**Cache Features**:
- Automatic expiration based on TTL
- Persistent storage using pickle
- MD5 hash-based cache keys
- Transparent to end user

**Disable caching**:
```python
manager = DataSourceManager(cache_enabled=False)
```

## Fallback Logic

The bot implements automatic fallback when a source fails:

1. **Price Data Fallback**: Yahoo Finance → FMP → Alpha Vantage
2. **Fundamentals Fallback**: FMP → Yahoo Finance
3. **Corporate Actions Fallback**: Yahoo Finance → FMP
4. **Macro Data Fallback**: FRED → World Bank → Quandl

Example:
```python
# Automatically tries Yahoo first, then FMP if Yahoo fails
price_data = manager.fetch_price_data(['AAPL'], start, end)
```

## API Key Acquisition

### Financial Modeling Prep (FMP)
1. Visit https://financialmodelingprep.com
2. Sign up for free or pro account
3. Get API key from dashboard
4. Free tier: ~250 calls/day

### Alpha Vantage
1. Visit https://www.alphavantage.co
2. Sign up and get API key via email
3. Free tier: 5 API calls per minute

### FRED
1. Visit https://fred.stlouisfed.org
2. Create free account
3. Get API key from account settings
4. No rate limits for registered users

### Quandl
1. Visit https://www.quandl.com
2. Create free account
3. Get API key from account
4. Free tier: Limited data access

## Performance Optimization

### Connection Pooling
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### Parallel Data Fetching
```python
from concurrent.futures import ThreadPoolExecutor

def fetch_multiple(symbols):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_symbol, s) for s in symbols]
        return [f.result() for f in futures]
```

### Database Optimization
Indexes are automatically created on:
- `symbol` (for symbol lookups)
- `date` (for date range queries)

For faster queries, consider:
```python
# Limit date ranges
df = ohlc.get_data('AAPL', start_date='2024-01-01', end_date='2024-12-31')

# Use parquet for large datasets
df.to_parquet('data/aapl_2024.parquet')
df = pd.read_parquet('data/aapl_2024.parquet')
```

## Troubleshooting

### Common Issues

**Issue**: API key not found
```
ERROR: FMP_API_KEY environment variable not set
```
**Solution**: Set environment variable before running setup
```bash
export FMP_API_KEY="your_key"
python setup_data_sources.py
```

**Issue**: Rate limit exceeded
```
ERROR: 429 Too Many Requests
```
**Solution**: 
- Reduce number of concurrent requests
- Increase delay between requests
- Use cache (enabled by default)
- Upgrade to paid API tier

**Issue**: No data returned
```
WARNING: All price data sources failed
```
**Solution**:
- Check internet connection
- Verify symbol exists (use `yfinance` directly)
- Check API key validity
- Review logs for specific error

### Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

manager = DataSourceManager()
data = manager.fetch_price_data(['AAPL'], start, end)
```

Check configuration:
```python
from src.data.data_sources_config import DataSourcesConfig

print(DataSourcesConfig.get_configuration_summary())
validation = DataSourcesConfig.validate_api_keys()
print(validation)
```

## Examples

### Complete Workflow

```python
from src.data.data_source_manager import DataSourceManager
from src.data.ohlc_pipeline import OHLCPipeline
from src.data.fundamentals_pipeline import FundamentalsPipeline
from datetime import datetime, timedelta

# Initialize managers
manager = DataSourceManager()
ohlc = OHLCPipeline()
fundamentals = FundamentalsPipeline()

symbols = ['AAPL', 'MSFT', 'GOOGL']

# 1. Fetch price data
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
prices = manager.fetch_price_data(symbols, start_date, end_date)

# 2. Store in OHLC database
ohlc.fetch_and_store(symbols, period='1y')

# 3. Fetch fundamentals
fund_data = manager.fetch_fundamentals(symbols)

# 4. Fetch corporate actions
actions = manager.fetch_corporate_actions(symbols)

# 5. Retrieve data for analysis
apple_prices = ohlc.get_data('AAPL', start_date='2024-01-01')
apple_fund = fundamentals.get_fundamentals('AAPL')

# 6. Use in trading logic
print(f"AAPL Latest Close: {apple_prices['close'].iloc[-1]}")
print(f"AAPL P/E Ratio: {apple_fund['pe_ratio']}")
```

## Next Steps

1. **Set up API keys** for desired data sources
2. **Run `setup_data_sources.py`** to initialize databases
3. **Verify connectivity** with test data
4. **Integrate into trading logic** using examples above
5. **Monitor cache** for optimal performance

For more information, see [README.md](./README.md) and source code documentation.
