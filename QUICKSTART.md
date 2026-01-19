# Quick Start Guide

## Setup Instructions

### 1. Install Dependencies

```bash
cd /workspaces/Trading_Bot01
pip install -e ".[dev]"
```

### 2. Verify Installation

```bash
python -c "import src; print('✓ Trading Bot modules installed')"
```

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Start Development

Check out examples in the sections below.

---

## Example 1: Create a Portfolio

```python
from src.core.portfolio import Portfolio
from src.core.position import Position, PositionSide
from datetime import datetime

# Create portfolio
portfolio = Portfolio(initial_capital=100000, name="MyPortfolio")

# Add position
position = Position(
    symbol="AAPL",
    quantity=100,
    entry_price=150.0,
    entry_time=datetime.now(),
    side=PositionSide.LONG
)
portfolio.add_position(position)

# Check P&L
summary = portfolio.get_summary({"AAPL": 155.0})
print(summary)
```

## Example 2: Load and Query Market Data

```python
from src.data.ohlc_pipeline import OHLCPipeline

# Create pipeline
pipeline = OHLCPipeline()

# Fetch data from Yahoo Finance (requires yfinance)
# pipeline.fetch_and_store(["AAPL", "MSFT"], period="1y")

# Query data
data = pipeline.get_latest("AAPL", bars=20)
print(data)
```

## Example 3: Generate Trading Signals

```python
from src.signals.signal_generator import SignalGenerator
import pandas as pd

gen = SignalGenerator()

# Create sample price series
prices = pd.Series([100, 101, 102, 101, 99, 98, 100, 102, 105, 107])

# Generate momentum signal
signal_type = gen.momentum_signal(prices, fast_period=3, slow_period=5)
print(f"Signal: {signal_type}")

# Create signal object
signal = gen.generate_signal(
    symbol="AAPL",
    signal_type=signal_type,
    strength=0.75,
    timestamp="2024-01-19",
    reason="Moving average crossover"
)
print(signal)
```

## Example 4: Risk Management

```python
from src.risk.risk_manager import RiskManager, RiskLimits
from src.risk.position_sizer import PositionSizer

# Setup risk manager
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
    position_value=8000,
    daily_pnl=-1000
)
print(f"Trade valid: {is_valid}, Reason: {reason}")

# Position sizing - Kelly Criterion
fraction = PositionSizer.kelly_criterion(
    win_rate=0.55,
    avg_win=2.0,
    avg_loss=1.0
)
print(f"Kelly fraction: {fraction:.2%}")
```

## Example 5: Execute Trades

```python
from src.execution.executor import TradeExecutor

# Create executor with realistic costs
executor = TradeExecutor(slippage_bps=2.0, commission_pct=0.001)

# Execute market order
result = executor.execute_market_order(
    symbol="AAPL",
    quantity=100,
    current_price=150.0
)

print(f"Execution price: {result.price:.2f}")
print(f"Commission: ${result.commission:.2f}")
print(f"Total cost: ${result.quantity * result.price + result.commission:.2f}")
```

## Example 6: Backtest

```python
from src.backtesting.backtest_engine import BacktestEngine
import pandas as pd

# Create backtest engine
engine = BacktestEngine(initial_capital=100000)

# Create sample returns
returns = pd.Series([0.01, -0.005, 0.015, -0.002, 0.008])

# Calculate metrics
metrics = engine.calculate_metrics(returns)
print(f"Total return: {metrics['total_return']:.2%}")
print(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max drawdown: {metrics['max_drawdown']:.2%}")
```

---

## Next Steps

1. Review [README.md](README.md) for full documentation
2. Check [config/trading_config.ini](config/trading_config.ini) to customize settings
3. Run `python main.py` to start the system
4. Explore `research.ipynb` for interactive analysis

## Architecture Overview

```
Portfolio Manager
├── Core Components
│   ├── Position Tracking
│   ├── Trade Recording
│   └── P&L Calculation
├── Data Layer
│   ├── OHLC Pipeline (SQLite)
│   └── Fundamentals Pipeline
├── Strategy Layer
│   ├── Signal Generation
│   ├── Signal Validation
│   └── Backtesting
├── Execution Layer
│   ├── Order Management
│   ├── Trade Execution
│   └── Slippage/Commission
└── Risk Layer
    ├── Risk Controls
    └── Position Sizing
```

---

For issues or questions, check the README or examine the module docstrings!
