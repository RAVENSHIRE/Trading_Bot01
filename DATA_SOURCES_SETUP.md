<!-- markdown -->
# Data Sources Configuration Guide

## Overview

The Trading Bot supports multiple data sources for:
- **Price Data**: Daily and intraday OHLCV data
- **Fundamentals**: Financial ratios (P/E, P/B, ROE, etc.)
- **Corporate Actions**: Dividends, stock splits
- **Macro Data**: Economic indicators (GDP, unemployment, etc.)
- **Reference Data**: Company profiles, index constituents

## Supported Data Sources

### Price Data
| Source | Free Tier | Rate Limit | Best For |
|--------|-----------|-----------|----------|
| Yahoo Finance | ✓ | 2,000/min | Primary source, no API key needed |
| Alpha Vantage | Limited | 5/min | Intraday data, technical indicators |
| FMP | Limited | 300/min | Comprehensive data, requires API key |

### Fundamentals
| Source | Free Tier | Rate Limit | Best For |
|--------|-----------|-----------|----------|
| Yahoo Finance | ✓ | 2,000/min | Quick fundamentals lookup |
| FMP | Limited | 300/min | Complete financial statements |

### Corporate Actions
| Source | Free Tier | Rate Limit | Coverage |
|--------|-----------|-----------|----------|
| Yahoo Finance | ✓ | 2,000/min | Dividends & splits (most reliable) |
| FMP | Limited | 300/min | All corporate actions |

### Macro Data
| Source | Free Tier | Rate Limit | Coverage |
|--------|-----------|-----------|----------|
| FRED | ✓ | 120/min | US economic data (90+ indicators) |
| World Bank | ✓ | 600/min | Global development data |
| Quandl | Limited | 300/min | Curated datasets |

---

## Setup Instructions

### 1. No API Key Setup (Yahoo Finance + FRED)

**This is the quickest start without any API keys!**

```bash
# Set environment variables (optional for FRED)
export FRED_API_KEY="your_fred_api_key"  # Get free key from https://fred.stlouisfed.org

# Run the trading bot
python3 main.py
```

**What you get:**
- ✓ Full price data from Yahoo Finance
- ✓ Fundamentals from Yahoo Finance
- ✓ Corporate actions (dividends & splits)
- ✓ US macro data from FRED

### 2. Financial Modeling Prep (FMP) Setup

Best for: Comprehensive financial data, company profiles, historical financials

```bash
# 1. Sign up at https://financialmodelingprep.com
#    - Free tier: 250 calls/day
#    - Paid: $9-99/month

# 2. Get your API key from dashboard

# 3. Set environment variable
export FMP_API_KEY="fmp_xxxxxxxxxxxxx"

# 4. Test the connection
python3 -c "from src.data.data_sources_config import DataSourcesConfig; print(DataSourcesConfig.get_configuration_summary())"
```

### 3. Alpha Vantage Setup

Best for: Intraday data, technical indicators

```bash
# 1. Sign up at https://www.alphavantage.co
#    - Free tier: 5 calls/minute (can upgrade)
#    - Paid: $9.99+/month

# 2. Get your API key

# 3. Set environment variable
export ALPHA_VANTAGE_KEY="your_alpha_vantage_key"
```

### 4. FRED Setup (Recommended for Macro Data)

Best for: US economic indicators, macro factors

```bash
# 1. Sign up at https://fred.stlouisfed.org (free account)

# 2. Request API key (instant, via email)

# 3. Set environment variable
export FRED_API_KEY="your_fred_api_key"

# Available indicators include:
# - GDP (GDP)
# - Unemployment Rate (UNRATE)
# - Fed Funds Rate (FEDFUNDS)
# - CPI (CPIAUCSL)
# - 10-Year Treasury Yield (DGS10)
# - VIX (VIXCLS)
```

### 5. Quandl Setup

Best for: Curated alternative data, crypto data

```bash
# 1. Sign up at https://www.quandl.com
#    - Free tier: limited datasets

# 2. Set environment variable
export QUANDL_API_KEY="your_quandl_api_key"
```

---

## Configuration

### Environment File (.env)

Create a `.env` file in the project root:

```env
# Price Data
FMP_API_KEY=fmp_xxxxxxxxxxxxx
ALPHA_VANTAGE_KEY=your_key

# Macro Data
FRED_API_KEY=your_fred_api_key
QUANDL_API_KEY=your_key

# Optional
DEBUG=False
LOG_LEVEL=INFO
```

Load it in your Python code:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Configuration File (config/trading_config.ini)

Key settings:

```ini
[default]
# Primary data sources (in fallback order)
PRICE_DATA_SOURCE=yahoo
FUNDAMENTALS_SOURCE=fmp
CORPORATE_ACTIONS_SOURCE=yahoo
MACRO_DATA_SOURCE=fred

# Caching
CACHE_ENABLED=true
PRICE_DATA_CACHE_TTL_DAYS=1
FUNDAMENTALS_CACHE_TTL_DAYS=7
CORPORATE_ACTIONS_CACHE_TTL_DAYS=30
MACRO_DATA_CACHE_TTL_DAYS=7

# API Rate Limiting
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5
```

---

## Usage Examples

### Fetch Price Data

```python
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager(cache_enabled=True)

# Fetch last 30 days of price data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

price_data = manager.fetch_price_data(
    symbols=['AAPL', 'MSFT', 'TSLA'],
    start_date=start_date,
    end_date=end_date,
    interval='1d'
)

print(price_data)
```

### Fetch Fundamentals

```python
# Get latest fundamentals
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT'])

print(f"AAPL P/E Ratio: {fundamentals['AAPL']['pe_ratio']}")
print(f"MSFT ROE: {fundamentals['MSFT']['roe']}")
```

### Fetch Corporate Actions

```python
# Get dividends and splits
actions = manager.fetch_corporate_actions(['AAPL', 'MSFT'])

for symbol, action_list in actions.items():
    for action in action_list:
        print(f"{symbol}: {action['type']} on {action['date']}")
```

### Fetch Macro Data

```python
from datetime import datetime, timedelta

# Get last year of economic data
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

macro_data = manager.fetch_macro_data(
    indicators=['GDP', 'UNRATE', 'DGS10', 'FEDFUNDS'],
    start_date=start_date,
    end_date=end_date
)

for indicator, df in macro_data.items():
    print(f"{indicator}: {df.shape[0]} data points")
```

---

## Best Practices

### 1. Use Fallback Sources
The system automatically falls back to alternative sources if the primary one fails. The priority order is:

```
Price Data: Yahoo Finance → FMP → Alpha Vantage
Fundamentals: FMP → Yahoo Finance
Corporate Actions: Yahoo Finance → FMP
Macro Data: FRED → World Bank → Quandl
```

### 2. Enable Caching
Always enable caching for production:

```python
manager = DataSourceManager(cache_enabled=True)
```

Cache TTLs:
- **Price Data**: 1 day (markets change daily)
- **Fundamentals**: 7 days (updated quarterly)
- **Corporate Actions**: 30 days (historical, rarely changes)
- **Macro Data**: 7 days (released weekly/monthly)

### 3. Handle API Rate Limits
For free tiers with strict limits:

```python
# Alpha Vantage: 5 calls/min
# Use Yahoo Finance for frequent queries
# Use Alpha Vantage for intraday data only
```

### 4. Validate Configuration

```python
from src.data.data_sources_config import DataSourcesConfig

# Check which sources are enabled
print(DataSourcesConfig.get_configuration_summary())

# Validate API keys
validation = DataSourcesConfig.validate_api_keys()
for source, has_key in validation.items():
    status = "✓" if has_key else "✗"
    print(f"{status} {source}")
```

---

## Troubleshooting

### "API key not found"

```bash
# Check environment variables
echo $FMP_API_KEY
echo $FRED_API_KEY

# Or set them in code
import os
os.environ['FMP_API_KEY'] = 'your_key'
```

### "Rate limit exceeded"

```python
# Use caching (enabled by default)
manager = DataSourceManager(cache_enabled=True)

# Or use alternative source
from src.data.data_sources_config import DataSourcesConfig
sources = DataSourcesConfig.get_fallback_sources('PRICE_DATA')
```

### "No data returned"

Check if:
1. Symbol is valid (try AAPL first)
2. Date range is correct
3. API key is valid
4. Service is not down

```python
# Test with known good symbol
price_data = manager.fetch_price_data(['AAPL'], start, end)
```

---

## Minimal Setup for Testing

If you just want to get started quickly:

```bash
# No API keys needed!
# Yahoo Finance works without authentication

python3 -c "
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()
end = datetime.now()
start = end - timedelta(days=30)
df = manager.fetch_price_data(['AAPL'], start, end)
print(df.head())
"
```

---

## Production Deployment

For production, use environment variables:

```bash
# Docker example
docker run \
  -e FMP_API_KEY="$FMP_API_KEY" \
  -e FRED_API_KEY="$FRED_API_KEY" \
  trading-bot:latest
```

Or AWS Secrets Manager:

```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='trading-bot/api-keys')
# Use secret['SecretString'] to get keys
```

---

## Summary

| Component | Minimum | Recommended | Enterprise |
|-----------|---------|-------------|------------|
| Price Data | Yahoo Finance | Yahoo + FMP | FMP + Alpha Vantage |
| Fundamentals | Yahoo | FMP | FMP + Bloomberg |
| Corporate Actions | Yahoo | Yahoo + FMP | FMP |
| Macro Data | FRED | FRED + World Bank | Multiple sources |
| Cost | $0 | $0-10/month | $50+/month |
| Rate Limit | Good | Excellent | Unlimited |

**Recommended Free Setup:**
- Price Data: Yahoo Finance
- Fundamentals: Yahoo Finance
- Corporate Actions: Yahoo Finance
- Macro Data: FRED (free API key)

Get started now with zero API keys! 🚀
