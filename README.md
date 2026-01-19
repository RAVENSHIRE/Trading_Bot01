# Trading Bot

Python-powered quantamental trading system with automated risk controls and real P&L tracking.

## Project Structure

```
Trading_Bot01/
├── src/
│   ├── core/                 # Core trading components
│   │   ├── portfolio.py      # Portfolio management
│   │   ├── position.py       # Position tracking
│   │   └── trade.py          # Trade execution records
│   ├── data/                 # Data management
│   │   ├── ohlc_pipeline.py  # OHLC data pipeline
│   │   └── fundamentals_pipeline.py  # Fundamentals data
│   ├── signals/              # Signal generation
│   │   ├── signal_generator.py
│   │   └── validator.py      # Signal validation & testing
│   ├── execution/            # Trade execution
│   │   ├── executor.py       # Order execution
│   │   └── order_manager.py  # Order management
│   ├── risk/                 # Risk management
│   │   ├── risk_manager.py   # Risk controls
│   │   └── position_sizer.py # Position sizing
│   └── backtesting/          # Backtesting framework
│       ├── backtest_engine.py
│       ├── walk_forward.py   # Walk-forward validation
│       └── permutation_test.py # Permutation testing
├── config/
│   ├── trading_config.ini    # Configuration
│   ├── config.py             # Config loader
│   └── logging_config.py     # Logging setup
├── tests/                    # Unit tests
├── data/                     # Data storage (OHLC, fundamentals)
├── logs/                     # Log files
├── main.py                   # Entry point
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## Key Features

### 1. Data Management
- **Persistent OHLC Pipeline**: High-performance SQLite-based storage for price data
- **Fundamentals Pipeline**: Store and retrieve company metrics (P/E, P/B, ROE, etc.)
- Built-in caching and indexing for fast queries

### 2. Signal Generation & Validation
- **Multiple Signal Strategies**:
  - Momentum (Moving Average Crossover)
  - Mean Reversion (Bollinger Bands)
  - Extensible framework for custom signals
- **Robust Validation**:
  - Walk-forward analysis for out-of-sample testing
  - Permutation tests for statistical significance
  - Correlation analysis vs. benchmarks

### 3. Risk Management
- **Automated Risk Controls**:
  - Position size limits (% of portfolio)
  - Leverage constraints
  - Daily loss limits
  - Sector exposure limits
- **Intelligent Position Sizing**:
  - Kelly Criterion
  - Volatility-adjusted sizing
  - Risk-based sizing

### 4. Trade Execution
- **Realistic Execution Model**:
  - Slippage modeling (basis points)
  - Commission calculations
  - Market and limit order types
- **Order Management**:
  - Order lifecycle tracking
  - Fill status monitoring
  - Order cancellation

### 5. Portfolio Management
- **Real-time P&L Tracking**:
  - Realized P&L from closed positions
  - Unrealized P&L from open positions
  - Total return calculation
- **Portfolio Metrics**:
  - NAV (Net Asset Value)
  - Leverage ratio
  - Position exposure analysis

### 6. Backtesting Framework
- **Comprehensive Performance Metrics**:
  - Sharpe ratio, max drawdown, win rate
  - Returns distribution analysis
- **Walk-Forward Testing**: Validate strategy robustness over time
- **Permutation Testing**: Ensure statistical significance

## Installation

```bash
# Clone repository
git clone <repo-url>
cd Trading_Bot01

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# (Optional) Setup data sources
python init_data_sources.py
```

## Data Sources

The Trading Bot supports multiple data sources for price data, fundamentals, corporate actions, and economic indicators. **No API keys required to get started** - Yahoo Finance works out of the box!

### Quick Start (No API Keys)

```python
from src.data import DataSourceManager
from datetime import datetime, timedelta

manager = DataSourceManager()

# Fetch price data
df = manager.fetch_price_data(
    symbols=['AAPL', 'MSFT'],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Fetch fundamentals
fundamentals = manager.fetch_fundamentals(['AAPL', 'MSFT'])

# Fetch corporate actions (dividends, splits)
actions = manager.fetch_corporate_actions(['AAPL'])
```

### Supported Data Sources

| Data Type | Free Sources | API Key Sources |
|-----------|--------------|-----------------|
| **Price Data** | Yahoo Finance | FMP, Alpha Vantage |
| **Fundamentals** | Yahoo Finance | Financial Modeling Prep |
| **Corporate Actions** | Yahoo Finance | FMP |
| **Macro Data** | World Bank, FRED* | Quandl |

*FRED requires free account creation

### Setup with API Keys (Optional)

```bash
# Interactive setup wizard
python init_data_sources.py

# Validate configuration
python init_data_sources.py --validate

# Test data fetching
python init_data_sources.py --test
```

For complete data source documentation, see:
- **Quick Reference**: [DATA_SOURCES_QUICK_REFERENCE.md](DATA_SOURCES_QUICK_REFERENCE.md)
- **Full Setup Guide**: [DATA_SOURCES_SETUP.md](DATA_SOURCES_SETUP.md)
- **Configuration Index**: [DATA_SOURCES_INDEX.md](DATA_SOURCES_INDEX.md)

## Quick Start

### 1. Configure the System

Edit `config/trading_config.ini`:
```ini
INITIAL_CAPITAL=100000
MAX_POSITION_SIZE=0.1
MAX_LEVERAGE=2.0
SLIPPAGE_BPS=2.0
COMMISSION_PCT=0.001
```

### 2. Load Market Data

```python
from src.data.ohlc_pipeline import OHLCPipeline

pipeline = OHLCPipeline()
symbols = ["AAPL", "MSFT", "GOOGL"]
pipeline.fetch_and_store(symbols, period="1y")
```

### 3. Generate Trading Signals

```python
from src.signals.signal_generator import SignalGenerator
import pandas as pd

generator = SignalGenerator()

# Get price data
prices = pd.Series([100, 101, 102, 101, 99, 98, 100, 102])

# Generate signal
signal_type = generator.momentum_signal(prices)
signal = generator.generate_signal(
    symbol="AAPL",
    signal_type=signal_type,
    strength=0.8,
    timestamp="2024-01-19",
    reason="Fast MA crossed above slow MA"
)
```

### 4. Manage Risk

```python
from src.risk.risk_manager import RiskManager, RiskLimits

limits = RiskLimits(
    max_position_size=0.1,
    max_leverage=2.0,
    max_daily_loss_pct=0.02
)
risk_mgr = RiskManager(limits)

# Validate trade
is_valid, reason = risk_mgr.validate_trade(
    portfolio_value=100000,
    gross_exposure=150000,
    position_value=10000,
    daily_pnl=-1000
)
```

### 5. Execute Trades

```python
from src.execution.executor import TradeExecutor

executor = TradeExecutor(slippage_bps=2.0, commission_pct=0.001)

result = executor.execute_market_order(
    symbol="AAPL",
    quantity=100,
    current_price=150.0
)
```

### 6. Track Portfolio Performance

```python
from src.core.portfolio import Portfolio

portfolio = Portfolio(initial_capital=100000)

# Get summary
summary = portfolio.get_summary({
    "AAPL": 155.0,
    "MSFT": 380.0
})
print(summary)
# Output: {
#   'initial_capital': 100000,
#   'nav': 105000,
#   'return_pct': 5.0,
#   'realized_pnl': 2000,
#   'unrealized_pnl': 3000,
#   'leverage': 1.5
# }
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Running the Bot

```bash
# Start trading bot (paper trading)
python main.py

# Or use in Jupyter notebook
jupyter lab research.ipynb
```

## Advanced Usage

### Walk-Forward Validation

```python
from src.backtesting.walk_forward import WalkForwardValidator

validator = WalkForwardValidator(
    total_period=504,  # 2 years
    train_period=252,  # 1 year
    test_period=63     # 3 months
)

results = validator.validate(data, strategy_func)
```

### Permutation Testing

```python
from src.backtesting.permutation_test import PermutationTester

tester = PermutationTester()
results = tester.test_significance(returns, num_permutations=1000)

print(f"P-value: {results['p_value']}")
print(f"Statistically significant: {results['significant']}")
```

## Performance Optimization

- SQLite database with proper indexing for fast queries
- Vectorized operations using pandas/numpy
- Efficient memory management for large datasets

## Configuration

All settings are in `config/trading_config.ini`:

```ini
# Risk Management
MAX_POSITION_SIZE=0.1        # 10% max per position
MAX_LEVERAGE=2.0             # Max 2x leverage
MAX_DAILY_LOSS_PCT=0.02      # 2% daily loss limit

# Execution
SLIPPAGE_BPS=2.0             # 2 basis points slippage
COMMISSION_PCT=0.001         # 0.1% commission

# Signal Parameters
FAST_MA_PERIOD=20
SLOW_MA_PERIOD=50
BOLLINGER_PERIOD=20
BOLLINGER_STD=2.0
```

## Environment Variables

Set in `.env` file:
```
ALPHA_VANTAGE_KEY=your_key
FRED_API_KEY=your_key
```

## Logging

Logs are stored in `logs/trading.log` with rotation:
- Max file size: 10MB
- Backup files: 5
- Log level: configurable (INFO, DEBUG, ERROR)

## Future Enhancements

- [ ] Live API integration (Alpaca, Interactive Brokers)
- [ ] Machine learning signal generation
- [ ] Advanced portfolio optimization
- [ ] Real-time monitoring dashboard
- [ ] Multi-asset class support
- [ ] Crypto trading integration

## Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test: `pytest tests/`
3. Commit: `git commit -am 'Add feature'`
4. Push: `git push origin feature/new-feature`
5. Create Pull Request

## License

MIT License - see LICENSE file

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Disclaimer**: This is an educational trading system for research purposes. Past performance does not guarantee future results. Always use proper risk management when trading with real capital.
