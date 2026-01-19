<!-- markdown -->
# Data Sources Quick Reference

## 🚀 Getting Started (2 minutes)

### No API Keys Required
Start with Yahoo Finance (no authentication):

```python
from src.data.data_source_manager import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()

# Fetch price data
df = manager.fetch_price_data(
    symbols=['AAPL', 'MSFT'],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
print(df.head())
```

### With API Keys
```bash
# Set environment variables
export FMP_API_KEY="your_key"
export FRED_API_KEY="your_key"

# Or run interactive setup
python3 init_data_sources.py
```

---

## 📊 Data Available

### Price Data (OHLCV)
```python
manager.fetch_price_data(
    symbols=['AAPL', 'MSFT'],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    interval='1d'  # '1d', '1h', '15m', etc.
)
```

**Returns:** DataFrame with Open, High, Low, Close, Volume, Adjusted Close

### Fundamentals
```python
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT'])

# Access like: fundamentals['AAPL']['pe_ratio']
# Fields: pe_ratio, pb_ratio, debt_to_equity, roe, roa, dividend_yield, market_cap
```

### Corporate Actions
```python
actions = manager.fetch_corporate_actions(['AAPL'])

# Returns: {
#   'AAPL': [
#     {'type': 'dividend', 'date': '2024-05-17', 'amount': 0.24},
#     {'type': 'split', 'date': '2020-08-31', 'ratio': 4.0}
#   ]
# }
```

### Macro Data
```python
macro = manager.fetch_macro_data(
    indicators=['GDP', 'UNRATE', 'DGS10'],
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Common indicators:
# - GDP: US Gross Domestic Product
# - UNRATE: Unemployment Rate
# - CPIAUCSL: Consumer Price Index
# - DGS10: 10-Year Treasury Yield
# - FEDFUNDS: Federal Funds Rate
# - VIXCLS: VIX (Volatility Index)
```

---

## 🔧 Configuration

### Via Environment Variables (.env)
```env
FMP_API_KEY=your_key
ALPHA_VANTAGE_KEY=your_key
FRED_API_KEY=your_key
QUANDL_API_KEY=your_key
```

### Via Config File (config/trading_config.ini)
```ini
[default]
PRICE_DATA_SOURCE=yahoo
FUNDAMENTALS_SOURCE=fmp
MACRO_DATA_SOURCE=fred
CACHE_ENABLED=true
```

---

## 🔗 Data Sources Hierarchy

**Price Data:**
1. Yahoo Finance (free, no auth)
2. FMP (requires API key)
3. Alpha Vantage (requires API key)

**Fundamentals:**
1. FMP (requires API key)
2. Yahoo Finance (free, no auth)

**Corporate Actions:**
1. Yahoo Finance (free, no auth)
2. FMP (requires API key)

**Macro Data:**
1. FRED (requires API key)
2. World Bank (free, no auth)
3. Quandl (requires API key)

---

## ✅ Validation & Testing

```bash
# Check configuration
python3 -c "from src.data import DataSourcesConfig; print(DataSourcesConfig.get_configuration_summary())"

# Validate API keys
python3 init_data_sources.py --validate

# Test data fetching
python3 init_data_sources.py --test
```

---

## 💾 Caching

**Automatic caching enabled by default:**

```python
# Caching is on
manager = DataSourceManager(cache_enabled=True)

# Disable if needed
manager = DataSourceManager(cache_enabled=False)
```

**Cache TTLs:**
- Price Data: 1 day
- Fundamentals: 7 days
- Corporate Actions: 30 days
- Macro Data: 7 days

**Cache Location:** `data/.cache/`

---

## 📈 Usage Examples

### Get Latest Market Data
```python
from datetime import datetime, timedelta

manager = DataSourceManager()
end = datetime.now()
start = end - timedelta(days=30)

df = manager.fetch_price_data(['AAPL'], start, end)
print(f"Latest close: ${df.iloc[-1]['Close']:.2f}")
```

### Screen for Value Stocks
```python
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT', 'GOOGL'])

for symbol, data in fundamentals.items():
    pe = data.get('pe_ratio', float('inf'))
    pb = data.get('pb_ratio', float('inf'))
    if pe < 20 and pb < 3:
        print(f"{symbol}: P/E={pe:.1f}, P/B={pb:.1f} (Value)")
```

### Track Dividends
```python
actions = manager.fetch_corporate_actions(['AAPL', 'MSFT', 'JNJ'])

for symbol, action_list in actions.items():
    dividends = [a for a in action_list if a['type'] == 'dividend']
    if dividends:
        total = sum(a['amount'] for a in dividends)
        print(f"{symbol}: {len(dividends)} dividends, total: ${total:.2f}")
```

### Get Economic Context
```python
from datetime import datetime, timedelta

manager = DataSourceManager()
end = datetime.now()
start = end - timedelta(days=365*10)

macro = manager.fetch_macro_data(
    ['GDP', 'UNRATE', 'DGS10'],
    start_date=start,
    end_date=end
)

for indicator, df in macro.items():
    latest = df.iloc[-1] if not df.empty else None
    print(f"{indicator}: {latest}")
```

---

## 🆓 Free Tier Options

| Source | Price | Limit | Setup |
|--------|-------|-------|-------|
| Yahoo Finance | Free | Unlimited | No API key |
| FRED | Free | 120/min | Free account + key |
| World Bank | Free | 600/min | No API key |

**Free setup for all data:**
```bash
# Get FRED API key (free, instant)
# https://fred.stlouisfed.org

export FRED_API_KEY="your_key"

# Run immediately
python3 init_data_sources.py
```

---

## ⚠️ Troubleshooting

### "No data returned"
- Check symbol validity (try AAPL)
- Verify date range is correct
- Check API key if using paid source
- Try alternative source: `DataSourcesConfig.get_fallback_sources(DataSourceType.PRICE_DATA)`

### "Rate limit exceeded"
- Enable caching (on by default)
- Use less frequent API calls
- Upgrade API plan if available
- Wait and retry

### "API key not found"
```bash
# Check env vars
echo $FMP_API_KEY

# Set in code
import os
os.environ['FMP_API_KEY'] = 'your_key'
```

---

## 📚 Full Documentation

See [DATA_SOURCES_SETUP.md](DATA_SOURCES_SETUP.md) for:
- Complete setup instructions
- API key registration
- Advanced configuration
- Production deployment

---

## 🎯 Next Steps

1. **Install dependencies:** `pip install -e ".[dev]"`
2. **Configure data sources:** `python3 init_data_sources.py`
3. **Test fetching:** `python3 init_data_sources.py --test`
4. **Start using:** See examples above

**Questions?** Check [DATA_SOURCES_SETUP.md](DATA_SOURCES_SETUP.md)
