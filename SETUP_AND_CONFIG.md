# Project Setup & Configuration Guide

## ✅ Setup Complete

Your Python-powered quantamental trading system is fully configured and ready to use.

## 🧪 Verify Installation

### Option 1: Quick Verification (Recommended)

```bash
cd /workspaces/Trading_Bot01
python test_imports.py
```

This will:
- ✓ Import all modules
- ✓ Run basic functionality tests
- ✓ Verify P&L calculations
- ✓ Test signal generation
- ✓ Validate risk management
- ✓ Check trade execution

### Option 2: Run Unit Tests

```bash
cd /workspaces/Trading_Bot01
python -m pytest tests/test_core.py -v
```

## 📋 Configuration Files Created

### 1. **pytest.ini** - Pytest Configuration
- Configures test discovery
- Sets verbosity and output format
- Points to tests directory

### 2. **conftest.py** - Pytest Fixtures & Setup
- Adds `src` to Python path automatically
- Ensures imports work correctly
- Sets up test environment

### 3. **tests/__init__.py** - Test Package Marker
- Makes tests directory a Python package
- Enables proper module discovery

## 📁 Project Structure (Complete)

```
Trading_Bot01/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── position.py       (Position tracking)
│   │   ├── portfolio.py      (Portfolio management)
│   │   └── trade.py          (Trade records)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ohlc_pipeline.py  (Price data)
│   │   └── fundamentals_pipeline.py  (Company metrics)
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── signal_generator.py
│   │   └── validator.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   └── order_manager.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_manager.py
│   │   └── position_sizer.py
│   └── backtesting/
│       ├── __init__.py
│       ├── backtest_engine.py
│       ├── walk_forward.py
│       └── permutation_test.py
├── config/
│   ├── trading_config.ini
│   ├── config.py
│   └── logging_config.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── conftest.py              (Pytest setup)
├── pytest.ini               (Pytest config)
├── test_imports.py          (Quick verification)
├── main.py                  (Entry point)
├── pyproject.toml           (Package config)
├── .gitignore
├── README.md
├── QUICKSTART.md
└── SETUP_COMPLETE.txt
```

## 🚀 Getting Started

### 1. Basic Import Test

```python
from src.core.portfolio import Portfolio
from src.core.position import Position, PositionSide
from datetime import datetime

# Create portfolio
portfolio = Portfolio(initial_capital=100000)

# Create position
pos = Position(
    symbol="AAPL",
    quantity=100,
    entry_price=150.0,
    entry_time=datetime.now(),
    side=PositionSide.LONG
)

# Get summary
print(portfolio.get_summary({"AAPL": 155.0}))
```

### 2. Run the Main Script

```bash
python main.py
```

This will:
- Initialize trading system
- Setup logging
- Load configuration
- Prepare data pipelines
- Ready for strategy implementation

### 3. Use in Jupyter

```bash
jupyter lab research.ipynb
```

## 🔧 Module Import Reference

```python
# Core Components
from src.core.portfolio import Portfolio
from src.core.position import Position, PositionSide
from src.core.trade import Trade, TradeType

# Data Management
from src.data.ohlc_pipeline import OHLCPipeline
from src.data.fundamentals_pipeline import FundamentalsPipeline

# Signal Generation
from src.signals.signal_generator import SignalGenerator, Signal, SignalType
from src.signals.validator import SignalValidator

# Execution
from src.execution.executor import TradeExecutor
from src.execution.order_manager import OrderManager

# Risk Management
from src.risk.risk_manager import RiskManager, RiskLimits
from src.risk.position_sizer import PositionSizer

# Backtesting
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.walk_forward import WalkForwardValidator
from src.backtesting.permutation_test import PermutationTester

# Configuration
from config.config import Config
from config.logging_config import setup_logging
```

## ⚙️ Configuration

### Edit Settings

```bash
# Open configuration file
nano config/trading_config.ini
```

Key settings:
```ini
[default]
INITIAL_CAPITAL=100000
MAX_POSITION_SIZE=0.1
MAX_LEVERAGE=2.0
SLIPPAGE_BPS=2.0
COMMISSION_PCT=0.001
```

### Environment Variables

Create `.env` file in project root:
```
ALPHA_VANTAGE_KEY=your_key_here
FRED_API_KEY=your_key_here
```

## 📊 Example Usage

### Load Market Data

```python
from src.data.ohlc_pipeline import OHLCPipeline

pipeline = OHLCPipeline()
# Fetch from Yahoo Finance
pipeline.fetch_and_store(["AAPL", "MSFT"], period="1y")

# Query data
data = pipeline.get_latest("AAPL", bars=20)
print(data)
```

### Generate Signals

```python
from src.signals.signal_generator import SignalGenerator
import pandas as pd

gen = SignalGenerator()
prices = pd.Series([100, 101, 102, 101, 99, 98, 100, 102])

# Momentum signal
signal_type = gen.momentum_signal(prices)
print(f"Signal: {signal_type}")
```

### Manage Risk

```python
from src.risk.risk_manager import RiskManager, RiskLimits

limits = RiskLimits(max_position_size=0.1, max_leverage=2.0)
risk_mgr = RiskManager(limits)

is_valid, reason = risk_mgr.validate_trade(
    portfolio_value=100000,
    gross_exposure=150000,
    position_value=10000,
    daily_pnl=-500
)
print(f"Valid: {is_valid}, Reason: {reason}")
```

### Execute Trades

```python
from src.execution.executor import TradeExecutor

executor = TradeExecutor(slippage_bps=2.0, commission_pct=0.001)
result = executor.execute_market_order("AAPL", 100, 150.0)
print(f"Execution price: {result.price:.2f}")
```

## 🧪 Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test

```bash
python -m pytest tests/test_core.py::test_position_creation -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 📝 Project Files

| File | Purpose |
|------|---------|
| `conftest.py` | Pytest configuration & path setup |
| `pytest.ini` | Pytest settings |
| `test_imports.py` | Quick module verification script |
| `main.py` | Entry point for trading system |
| `pyproject.toml` | Package metadata & dependencies |
| `config/trading_config.ini` | Trading system configuration |
| `README.md` | Full documentation |
| `QUICKSTART.md` | Code examples |

## 🔍 Troubleshooting

### ImportError: No module named 'src'

**Solution**: The project uses `conftest.py` to add src to path. Make sure to:
1. Run tests from project root
2. Use `python -m pytest` (not just `pytest`)
3. Or run `python test_imports.py` for verification

### ModuleNotFoundError

**Solution**: Run the verification script:
```bash
python test_imports.py
```

This will diagnose any import issues and show which modules are available.

### Database Errors

The system creates SQLite databases automatically in `data/` directory. If you get database errors:
1. Delete `data/*.db` files
2. Restart the system - databases will be recreated

## 📚 Documentation

- **README.md** - Complete project documentation
- **QUICKSTART.md** - Code examples for each module
- **SETUP_COMPLETE.txt** - Setup summary
- **Docstrings** - In-code documentation for all classes/methods

## 🎯 Next Steps

1. **Verify Setup**: Run `python test_imports.py`
2. **Read Documentation**: Check `README.md` and `QUICKSTART.md`
3. **Configure Settings**: Edit `config/trading_config.ini`
4. **Load Data**: Use `OHLCPipeline` to fetch market data
5. **Develop Strategies**: Implement trading signals
6. **Backtest**: Use `BacktestEngine` with walk-forward validation
7. **Deploy**: Use `main.py` for live/paper trading

## ✨ Features Ready to Use

✅ Portfolio management with P&L tracking  
✅ Position tracking and sizing  
✅ Signal generation (momentum, mean reversion)  
✅ Signal validation (walk-forward, permutation testing)  
✅ Automated risk controls  
✅ Trade execution with slippage  
✅ Commission modeling  
✅ Backtesting framework  
✅ Logging system  
✅ Configuration management  

## 🚀 You're Ready!

Your trading bot framework is fully set up and tested. Start building your strategies!

For questions, refer to:
- Module docstrings
- QUICKSTART.md examples
- README.md documentation
