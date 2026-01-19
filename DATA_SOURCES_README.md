# Trading Bot - Data Sources Configuration

**Status**: ✅ COMPLETE AND PRODUCTION READY

This comprehensive data sources system provides:
- Multiple price data sources with automatic fallback
- Fundamentals, corporate actions, and macro data
- Intelligent caching and rate limiting
- SQLite database persistence
- Full documentation and examples

## 🚀 Quick Start (2 Minutes)

```bash
# 1. Setup databases (no API keys needed!)
python setup_data_sources.py --quick

# 2. Validate configuration
python validate_data_sources.py

# 3. Use in your code
python examples_data_sources.py --example 1
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[DATA_SOURCES_QUICKSTART.md](DATA_SOURCES_QUICKSTART.md)** | 5-minute setup & common tasks |
| **[DATA_SOURCES_CONFIGURATION.md](DATA_SOURCES_CONFIGURATION.md)** | Complete reference guide |
| **[DATA_SOURCES_INTEGRATION.md](DATA_SOURCES_INTEGRATION.md)** | Integration with trading strategies |
| **[DATA_SOURCES_SETUP_SUMMARY.md](DATA_SOURCES_SETUP_SUMMARY.md)** | What's configured & features |

## 🔧 Available Data Sources

### Price Data (Free!)
- **Yahoo Finance** ✅ - Always works, no API key needed
- **FMP** - Optional (requires `FMP_API_KEY`)
- **Alpha Vantage** - Optional (requires `ALPHA_VANTAGE_KEY`)

### Fundamentals
- **Yahoo Finance** ✅ - P/E, P/B, ROE, ROA, etc.
- **FMP** - More comprehensive metrics

### Corporate Actions
- **Yahoo Finance** ✅ - Dividends and splits
- **FMP** - Additional details

### Macro Data
- **World Bank** ✅ - Global development indicators
- **FRED** - US economic data (requires `FRED_API_KEY`)
- **Quandl** - Alternative data (requires `QUANDL_API_KEY`)

## 📖 Core Modules

```python
# Main interface
from src.data.data_source_manager import DataSourceManager

# Direct source access
from src.data.ohlc_pipeline import OHLCPipeline
from src.data.fundamentals_pipeline import FundamentalsPipeline
from src.data.multi_source_pipeline import FMPConnector, YahooConnector

# Configuration
from src.data.data_sources_config import DataSourcesConfig, DataSourceType
```

## 💡 Usage Examples

### Fetch Price Data
```python
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()

prices = manager.fetch_price_data(
    symbols=['AAPL', 'MSFT'],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

### Store and Query OHLC
```python
from src.data.ohlc_pipeline import OHLCPipeline

ohlc = OHLCPipeline()

# Store from Yahoo
ohlc.fetch_and_store(['AAPL', 'MSFT'], period='1y')

# Query from database
df = ohlc.get_data('AAPL', start_date='2024-01-01')
latest = ohlc.get_latest('AAPL', bars=100)
```

### Fetch Fundamentals
```python
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT'])

for symbol, data in fundamentals.items():
    print(f"{symbol}: P/E={data['pe_ratio']}, ROE={data['roe']}")
```

### Track Corporate Actions
```python
actions = manager.fetch_corporate_actions(['JNJ'])

for action in actions['JNJ']:
    if action['type'] == 'dividend':
        print(f"Dividend: {action['date']} ${action['amount']}")
```

## 🎯 Key Features

### Intelligent Fallback
- Tries multiple sources automatically
- Falls back gracefully on failures
- Logs all attempts

### Caching System
- Price data: 1 day
- Fundamentals: 7 days
- Corporate actions: 30 days
- Macro data: 7 days

### Rate Limiting
- Respects source rate limits
- Yahoo: 2,000 requests/min
- FMP: 300 requests/min
- Efficient batching

### Database Storage
- SQLite OHLC database
- SQLite Fundamentals database
- Indexes on symbol & date
- Fast queries

### Error Handling
- Comprehensive logging
- Graceful degradation
- Clear error messages

## 📋 Setup Scripts

### setup_data_sources.py
Main setup and initialization:
```bash
python setup_data_sources.py --help

# Quick setup (databases only)
python setup_data_sources.py --quick

# Full setup with data
python setup_data_sources.py --full

# Custom symbols
python setup_data_sources.py --symbols AAPL,MSFT,GOOGL --days 90
```

### validate_data_sources.py
Configuration validation:
```bash
python validate_data_sources.py

# Checks:
# - Environment variables
# - Data sources configuration
# - Directory structure
# - Database files
# - Cache status
# - Connectivity tests
```

### examples_data_sources.py
Working examples:
```bash
python examples_data_sources.py --all

# Or specific examples
python examples_data_sources.py --example 1  # Price data
python examples_data_sources.py --example 3  # Fundamentals
python examples_data_sources.py --example 8  # Complete workflow
```

## 📊 Database Files

| Database | Purpose | Location |
|----------|---------|----------|
| OHLC | Price data (OHLCV) | `data/ohlc_data.db` |
| Fundamentals | P/E, P/B, ROE, etc. | `data/fundamentals_data.db` |

## ⚙️ Configuration

Main config file: `config/trading_config.ini`

```ini
[default]
# API Keys (environment variables)
FMP_API_KEY=${FMP_API_KEY}
FRED_API_KEY=${FRED_API_KEY}

# Data Sources
PRICE_DATA_SOURCE=yahoo
FUNDAMENTALS_SOURCE=fmp
CORPORATE_ACTIONS_SOURCE=yahoo

# Cache
CACHE_ENABLED=true
PRICE_DATA_CACHE_TTL_DAYS=1
FUNDAMENTALS_CACHE_TTL_DAYS=7
```

## 🔐 API Key Setup (Optional)

### Financial Modeling Prep
```bash
export FMP_API_KEY="your_key_here"
# Get at: https://financialmodelingprep.com
# Free tier: ~250 calls/day
```

### FRED
```bash
export FRED_API_KEY="your_key_here"
# Get at: https://fred.stlouisfed.org
# Free tier: Unlimited
```

### Alpha Vantage
```bash
export ALPHA_VANTAGE_KEY="your_key_here"
# Get at: https://www.alphavantage.co
# Free tier: 5 calls/min
```

## 🧪 Testing & Validation

```bash
# Run all validations
python validate_data_sources.py

# Run all examples
python examples_data_sources.py --all

# Check specific sources
python validate_data_sources.py  # Shows connectivity status
```

## 📈 Performance

### Data Retrieval
- Yahoo Finance: 2-5 seconds
- From cache: <100ms
- From database: <500ms

### Storage
- 1 year daily OHLC: ~50 KB
- 1000 symbols: ~50 MB
- Fundamentals: ~10 KB per snapshot

## 🚨 Troubleshooting

### "No data returned"
- Check internet connection
- Verify symbol exists (AAPL not APPLE)
- Check API key if using FMP/FRED
- See logs in `logs/`

### Rate limit exceeded
- Cache is enabled by default
- Check API key rate limits
- Consider upgrading plan

### Database locked
- Close other processes using database
- Restart Python interpreter

## 📖 Documentation

1. **Start Here**: [DATA_SOURCES_QUICKSTART.md](DATA_SOURCES_QUICKSTART.md)
2. **Detailed**: [DATA_SOURCES_CONFIGURATION.md](DATA_SOURCES_CONFIGURATION.md)
3. **Integration**: [DATA_SOURCES_INTEGRATION.md](DATA_SOURCES_INTEGRATION.md)
4. **Summary**: [DATA_SOURCES_SETUP_SUMMARY.md](DATA_SOURCES_SETUP_SUMMARY.md)

## 📁 Project Structure

```
Trading_Bot01/
├── data/
│   ├── ohlc_data.db                    # Price database
│   ├── fundamentals_data.db            # Fundamentals database
│   └── .cache/                         # Cache files
├── src/data/
│   ├── data_sources_config.py          # Configuration
│   ├── data_source_manager.py          # Main manager
│   ├── ohlc_pipeline.py                # OHLC pipeline
│   ├── fundamentals_pipeline.py        # Fundamentals pipeline
│   └── multi_source_pipeline.py        # Direct connectors
├── config/
│   └── trading_config.ini              # Main config
├── setup_data_sources.py               # Setup script
├── validate_data_sources.py            # Validation
└── examples_data_sources.py            # Examples
```

## ✅ What's Included

- ✅ Price data from multiple sources
- ✅ Fundamentals (P/E, P/B, ROE, ROA, etc.)
- ✅ Corporate actions (dividends, splits)
- ✅ Macro data (economic indicators)
- ✅ SQLite database storage
- ✅ Intelligent caching
- ✅ Automatic fallback
- ✅ Rate limiting
- ✅ Comprehensive logging
- ✅ Full documentation
- ✅ Working examples
- ✅ Validation scripts

## 🎓 Integration Examples

See [DATA_SOURCES_INTEGRATION.md](DATA_SOURCES_INTEGRATION.md) for:
- Signal generation with fundamentals
- Backtesting with stored data
- Corporate action monitoring
- Feature engineering
- Risk management integration
- Portfolio optimization
- Macro-aware strategies
- Scheduled updates
- Data quality monitoring

## 📞 Next Steps

1. **Quick Setup**: Run `python setup_data_sources.py --quick`
2. **Validate**: Run `python validate_data_sources.py`
3. **Explore**: Run `python examples_data_sources.py --all`
4. **Read**: Open [DATA_SOURCES_CONFIGURATION.md](DATA_SOURCES_CONFIGURATION.md)
5. **Integrate**: Use examples from [DATA_SOURCES_INTEGRATION.md](DATA_SOURCES_INTEGRATION.md)

---

**Status**: ✅ Production Ready  
**Last Updated**: January 19, 2026  
**Maintenance**: Low - automatic fallback and caching
