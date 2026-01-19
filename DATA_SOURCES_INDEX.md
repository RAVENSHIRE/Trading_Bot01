<!-- markdown -->
# Data Sources Configuration - Index

## 📋 Complete Overview

This index helps you navigate all data source configuration files and understand what's available.

---

## 📁 Files Added

### Core Modules
| File | Purpose | Lines |
|------|---------|-------|
| `src/data/data_sources_config.py` | Configuration and data source definitions | 250+ |
| `src/data/data_source_manager.py` | Main interface for fetching data | 500+ |

### Setup & Examples
| File | Purpose | Usage |
|------|---------|-------|
| `init_data_sources.py` | Interactive setup wizard | `python3 init_data_sources.py` |
| `examples_data_sources.py` | 7 runnable examples | `python3 examples_data_sources.py` |

### Documentation
| File | Purpose | Read Time |
|------|---------|-----------|
| `DATA_SOURCES_QUICK_REFERENCE.md` | Quick start & common patterns | 5 min |
| `DATA_SOURCES_SETUP.md` | Complete setup guide | 20 min |
| `DATA_SOURCES_CONFIGURATION_SUMMARY.md` | What was added & why | 10 min |

### Configuration
| File | Purpose | Changed |
|------|---------|---------|
| `config/trading_config.ini` | Trading configuration | Updated |
| `src/data/__init__.py` | Data module exports | Updated |

---

## 🗺️ Navigation Guide

### I want to...

#### Get Started Immediately (5 minutes)
1. Read: [DATA_SOURCES_QUICK_REFERENCE.md](DATA_SOURCES_QUICK_REFERENCE.md)
2. Run: `python3 init_data_sources.py`
3. Use: See "Usage Examples" in quick reference

#### Set Up with API Keys (10 minutes)
1. Read: [DATA_SOURCES_SETUP.md](DATA_SOURCES_SETUP.md) - Setup section
2. Run: `python3 init_data_sources.py`
3. Validate: `python3 init_data_sources.py --validate`

#### Understand What Was Added (10 minutes)
1. Read: [DATA_SOURCES_CONFIGURATION_SUMMARY.md](DATA_SOURCES_CONFIGURATION_SUMMARY.md)
2. Review: File structure and design decisions

#### See Working Examples (5 minutes)
```bash
python3 examples_data_sources.py        # Run all 7 examples
python3 examples_data_sources.py 1      # Just price data
python3 examples_data_sources.py 2      # Just fundamentals
```

#### Use in My Trading Strategy (5 minutes)
See [DATA_SOURCES_QUICK_REFERENCE.md#-usage-examples](DATA_SOURCES_QUICK_REFERENCE.md#-usage-examples)

```python
from src.data import DataSourceManager

manager = DataSourceManager()
price_data = manager.fetch_price_data(['AAPL'], ...)
```

#### Integrate with Production System (20 minutes)
1. Read: [DATA_SOURCES_SETUP.md#production-deployment](DATA_SOURCES_SETUP.md#production-deployment)
2. Configure environment variables
3. Set up caching
4. Test with `python3 init_data_sources.py --test`

---

## 📚 Documentation by Data Type

### Price Data (OHLCV)
- **Quick Start**: [QUICK_REFERENCE.md#-price-data](DATA_SOURCES_QUICK_REFERENCE.md#-data-available)
- **Full Setup**: [SETUP.md#price-data](DATA_SOURCES_SETUP.md#price-data)
- **Example**: [examples_data_sources.py:example_1_price_data](examples_data_sources.py)

### Fundamentals
- **Quick Start**: [QUICK_REFERENCE.md#-data-available](DATA_SOURCES_QUICK_REFERENCE.md#-data-available)
- **Full Setup**: [SETUP.md#fundamentals](DATA_SOURCES_SETUP.md)
- **Example**: [examples_data_sources.py:example_2_fundamentals](examples_data_sources.py)
- **Configuration**: [data_sources_config.py:FMP_FUNDAMENTALS](src/data/data_sources_config.py)

### Corporate Actions
- **Quick Start**: [QUICK_REFERENCE.md#-data-available](DATA_SOURCES_QUICK_REFERENCE.md#-data-available)
- **Full Setup**: [SETUP.md#corporate-actions](DATA_SOURCES_SETUP.md)
- **Example**: [examples_data_sources.py:example_3_corporate_actions](examples_data_sources.py)

### Macro Data
- **Quick Start**: [QUICK_REFERENCE.md#-data-available](DATA_SOURCES_QUICK_REFERENCE.md#-data-available)
- **Full Setup**: [SETUP.md#macro-data](DATA_SOURCES_SETUP.md)
- **Example**: [examples_data_sources.py:example_4_macro_data](examples_data_sources.py)

---

## 🔗 Quick Links by Data Source

### Yahoo Finance
- Free API (no key needed)
- [Quick Reference](DATA_SOURCES_QUICK_REFERENCE.md#-free-tier-options)
- [Full Setup](DATA_SOURCES_SETUP.md#minimal-setup-for-testing)
- [Example](examples_data_sources.py)

### Financial Modeling Prep (FMP)
- API Key: https://financialmodelingprep.com
- [Setup Instructions](DATA_SOURCES_SETUP.md#2-financial-modeling-prep-fmp-setup)
- [Configuration](src/data/data_sources_config.py)
- Cost: Free ($0-$99/month)

### Alpha Vantage
- API Key: https://www.alphavantage.co
- [Setup Instructions](DATA_SOURCES_SETUP.md#3-alpha-vantage-setup)
- Best For: Intraday data
- Cost: Free ($9.99+/month)

### FRED (Federal Reserve Data)
- API Key: https://fred.stlouisfed.org (instant, free)
- [Setup Instructions](DATA_SOURCES_SETUP.md#4-fred-setup-recommended-for-macro-data)
- [Example](examples_data_sources.py)
- Best For: US economic indicators

### World Bank
- No API Key needed
- [Documentation](DATA_SOURCES_SETUP.md#supported-data-sources)
- Best For: Global development data
- Cost: Free

### Quandl
- API Key: https://www.quandl.com
- [Setup Instructions](DATA_SOURCES_SETUP.md#5-quandl-setup)
- Best For: Alternative data, crypto
- Cost: Free (limited) - $99+/month

---

## 🎯 Common Tasks

### Task: Fetch daily price data for backtesting
```python
from src.data import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()
df = manager.fetch_price_data(
    ['AAPL', 'MSFT'],
    datetime(2020, 1, 1),
    datetime(2024, 12, 31)
)
```
📖 See: [examples_data_sources.py#example_1](examples_data_sources.py)

### Task: Screen for value stocks
```python
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT', ...])
for symbol, data in fundamentals.items():
    if data['pe_ratio'] < 20:
        print(f"{symbol} is a value stock")
```
📖 See: [examples_data_sources.py#example_2](examples_data_sources.py)

### Task: Check dividend history
```python
actions = manager.fetch_corporate_actions(['JNJ', 'PG'])
dividends = [a for a in actions['JNJ'] if a['type'] == 'dividend']
```
📖 See: [examples_data_sources.py#example_3](examples_data_sources.py)

### Task: Get economic context
```python
macro = manager.fetch_macro_data(['GDP', 'UNRATE'], start, end)
```
📖 See: [examples_data_sources.py#example_4](examples_data_sources.py)

### Task: Check current configuration
```python
from src.data import DataSourcesConfig
print(DataSourcesConfig.get_configuration_summary())
```
📖 See: [examples_data_sources.py#example_5](examples_data_sources.py)

---

## 🔍 API Reference

### Main Interface: DataSourceManager

```python
from src.data import DataSourceManager

manager = DataSourceManager(cache_enabled=True)

# Methods:
manager.fetch_price_data(symbols, start_date, end_date, interval)
manager.fetch_fundamentals(symbols, date=None)
manager.fetch_corporate_actions(symbols, start_date, end_date)
manager.fetch_macro_data(indicators, start_date, end_date)
```

### Configuration: DataSourcesConfig

```python
from src.data import DataSourcesConfig, DataSourceType

# Get enabled sources for a type
sources = DataSourcesConfig.get_sources_by_type(DataSourceType.PRICE_DATA)

# Get primary source
primary = DataSourcesConfig.get_primary_source(DataSourceType.PRICE_DATA)

# Validate API keys
validation = DataSourcesConfig.validate_api_keys()

# Get configuration summary
summary = DataSourcesConfig.get_configuration_summary()
```

📖 Full API: [src/data/data_sources_config.py](src/data/data_sources_config.py)
📖 Implementation: [src/data/data_source_manager.py](src/data/data_source_manager.py)

---

## ⚙️ Configuration

### Environment Variables (.env)
```env
FMP_API_KEY=your_key
ALPHA_VANTAGE_KEY=your_key
FRED_API_KEY=your_key
QUANDL_API_KEY=your_key
```

### Config File (config/trading_config.ini)
```ini
[default]
PRICE_DATA_SOURCE=yahoo
CACHE_ENABLED=true
PRICE_DATA_CACHE_TTL_DAYS=1
```

📖 See: [DATA_SOURCES_SETUP.md#configuration](DATA_SOURCES_SETUP.md#configuration)

---

## 🧪 Testing & Validation

### Check Configuration
```bash
python3 init_data_sources.py --validate
```

### Test Data Fetching
```bash
python3 init_data_sources.py --test
```

### Run Examples
```bash
python3 examples_data_sources.py     # All 7 examples
python3 examples_data_sources.py 1   # Price data only
```

---

## 📊 Supported Data Sources Summary

| Type | Primary | Fallback 1 | Fallback 2 | Free |
|------|---------|-----------|-----------|------|
| **Price Data** | Yahoo ✓ | FMP | Alpha Vantage | Yes |
| **Fundamentals** | FMP | Yahoo ✓ | - | Yes* |
| **Corporate Actions** | Yahoo ✓ | FMP | - | Yes |
| **Macro Data** | FRED | World Bank ✓ | Quandl | Yes* |

*Free with optional API key for enhanced features

---

## 💾 Caching Strategy

| Data Type | TTL | Location |
|-----------|-----|----------|
| Price Data | 1 day | data/.cache/ |
| Fundamentals | 7 days | data/.cache/ |
| Corporate Actions | 30 days | data/.cache/ |
| Macro Data | 7 days | data/.cache/ |

---

## 🚀 Quick Start Checklist

- [ ] Read [DATA_SOURCES_QUICK_REFERENCE.md](DATA_SOURCES_QUICK_REFERENCE.md)
- [ ] Run `python3 init_data_sources.py` (optional)
- [ ] Run `python3 init_data_sources.py --validate`
- [ ] Run `python3 init_data_sources.py --test`
- [ ] Run `python3 examples_data_sources.py`
- [ ] Start using in your code!

---

## 📞 Support

### Issues?
1. Check [DATA_SOURCES_QUICK_REFERENCE.md#troubleshooting](DATA_SOURCES_QUICK_REFERENCE.md#troubleshooting)
2. Check [DATA_SOURCES_SETUP.md#troubleshooting](DATA_SOURCES_SETUP.md#troubleshooting)
3. Run `python3 init_data_sources.py --test`

### Want more data sources?
The system is designed to be extensible. See [DATA_SOURCES_SETUP.md](DATA_SOURCES_SETUP.md) for adding new sources.

---

## 📈 Next Steps

1. **For beginners**: Start with [DATA_SOURCES_QUICK_REFERENCE.md](DATA_SOURCES_QUICK_REFERENCE.md)
2. **For setup**: Run `python3 init_data_sources.py`
3. **For examples**: Run `python3 examples_data_sources.py`
4. **For integration**: See usage examples in quick reference
5. **For production**: See [DATA_SOURCES_SETUP.md#production-deployment](DATA_SOURCES_SETUP.md#production-deployment)

---

## ✅ Summary

You now have:
- ✓ **4 data types** (price, fundamentals, corporate actions, macro)
- ✓ **6+ data sources** with intelligent fallback
- ✓ **Automatic caching** for performance
- ✓ **Interactive setup** wizard
- ✓ **7 working examples**
- ✓ **Comprehensive documentation**
- ✓ **Zero API key option** (Yahoo Finance)

**Ready to start trading! 🚀**
