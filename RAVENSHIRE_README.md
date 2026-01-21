# Ravenshire Intelligence Engine

**Institutional-Grade Quantitative Trading Infrastructure**

A sophisticated, production-ready quantitative hedge fund infrastructure built on a 5-layer architecture with autonomous agents, machine learning, and real-time monitoring.

---

## 🏗️ Architecture Overview

### 5-Layer Hedge Fund Architecture

```
┌─────────────────────────────────────────────────────┐
│  Layer 5: Orchestration Layer                       │
│  (Prefect Workflows, Scheduling, Monitoring)        │
├─────────────────────────────────────────────────────┤
│  Layer 4: Execution & Monitoring Layer              │
│  (Trade Execution, Live Monitoring, Drift Detection)│
├─────────────────────────────────────────────────────┤
│  Layer 3: Portfolio & Risk Layer                    │
│  (Portfolio Optimization, Risk Management)          │
├─────────────────────────────────────────────────────┤
│  Layer 2: Research Layer                            │
│  (Backtesting, MLflow, Parameter Optimization)      │
├─────────────────────────────────────────────────────┤
│  Layer 1: Data Layer                                │
│  (Data Versioning, Caching, Validation)             │
└─────────────────────────────────────────────────────┘
```

### Multi-Agent System

Five specialized agents coordinate to make trading decisions:

- **Oracle Agent** 🔮 - Market regime detection and macro analysis
- **Analyst Agent** 📊 - Alpha generation and signal creation
- **Strategist Agent** 🎯 - Portfolio optimization and rebalancing
- **Sentinel Agent** 🛡️ - Risk veto and compliance checks
- **Sovereign Agent** 👑 - Final decision authority

---

## 📦 Project Structure

```
Trading_Bot01/
├── src/
│   ├── agents/                    # Multi-agent system
│   │   ├── base_agent.py
│   │   ├── oracle.py
│   │   ├── analyst.py
│   │   ├── strategist.py
│   │   ├── sentinel.py
│   │   └── __init__.py
│   ├── data/                      # Data layer
│   │   ├── data_manager.py        # Versioning, caching, validation
│   │   └── __init__.py
│   ├── research/                  # Research layer
│   │   ├── backtest_engine.py     # Backtesting with MLflow
│   │   └── __init__.py
│   ├── portfolio/                 # Portfolio & risk layer
│   │   ├── portfolio_manager.py   # Optimization, risk monitoring
│   │   └── __init__.py
│   ├── execution/                 # Execution layer
│   │   ├── live_executor.py       # Trade execution, monitoring
│   │   └── __init__.py
│   ├── ml/                        # Machine learning models
│   │   ├── regime_detector.py
│   │   ├── clustering.py
│   │   └── __init__.py
│   ├── orchestration/             # Orchestration layer
│   │   ├── workflow_manager.py    # Workflow scheduling
│   │   ├── agent_coordinator.py   # Agent communication
│   │   └── __init__.py
│   └── main.py                    # Entry point
├── dashboard/                     # 3D React Dashboard
│   ├── app.py
│   └── ...
├── config/                        # Configuration
│   └── trading_config.ini
├── tests/                         # Unit tests
│   ├── test_imports.py
│   └── ...
├── AEGIS_III_ARCHITECTURE.md      # Architecture documentation
├── VIDEO_ANALYSIS_IMPLEMENTATION.md # Quant Science video analysis
└── requirements-aegis.txt         # Extended dependencies
```

---

## 🚀 Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/RAVENSHIRE/Trading_Bot01.git
cd Trading_Bot01

# Install dependencies
pip install -r requirements-aegis.txt

# Optional: Install MLflow for experiment tracking
pip install mlflow

# Optional: Install Prefect for workflow orchestration
pip install prefect
```

### Quick Start

```python
from src.data.data_manager import DataManager
from src.research.backtest_engine import ResearchManager
from src.portfolio.portfolio_manager import PortfolioManager
from src.execution.live_executor import ExecutionManager
from src.orchestration.workflow_manager import OrchestrationManager

# Initialize managers
data_manager = DataManager()
research_manager = ResearchManager()
portfolio_manager = PortfolioManager(initial_capital=100000)
execution_manager = ExecutionManager()
orchestration_manager = OrchestrationManager()

# Fetch market data
data = data_manager.get_market_data(
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2024-01-01",
    end_date="2026-01-20"
)

# Run backtest
result = research_manager.backtest_strategy(
    strategy_func=your_strategy,
    data=data,
    parameters={"ma_period": 20},
    strategy_name="MA_Crossover"
)

print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Total Return: {result.total_return:.2%}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
```

---

## 📊 Layer Details

### Layer 1: Data Layer

**Responsibilities:**
- Data collection from multiple sources
- Data versioning for reproducibility
- Caching for performance
- Quality validation

**Key Classes:**
- `DataManager` - Main interface
- `DataVersioning` - Version control for datasets
- `DataCache` - In-memory caching
- `DataValidator` - Quality checks
- `MultiSourceFetcher` - Multi-source data fetching

```python
# Example: Data versioning
data = data_manager.get_market_data(
    symbols=["AAPL", "MSFT"],
    start_date="2024-01-01",
    end_date="2026-01-20",
    create_version=True  # Creates versioned snapshot
)
```

### Layer 2: Research Layer

**Responsibilities:**
- Strategy development and backtesting
- Parameter optimization
- Experiment tracking (MLflow)
- Statistical validation

**Key Classes:**
- `ResearchManager` - Main interface
- `BacktestRunner` - Executes backtests
- `ParameterOptimizer` - Hyperparameter tuning (Optuna)
- `PerformanceCalculator` - Metrics calculation

```python
# Example: Backtest with MLflow tracking
result = research_manager.backtest_strategy(
    strategy_func=my_strategy,
    data=data,
    parameters={"ma_period": 20, "threshold": 0.02},
    strategy_name="MA_Crossover"
)

# Optimize parameters
best_params = research_manager.optimize_parameters(
    strategy_func=my_strategy,
    data=data,
    param_space={
        "ma_period": (10, 50, 5),
        "threshold": (0.01, 0.05, 0.01)
    },
    strategy_name="MA_Crossover",
    n_trials=50
)
```

### Layer 3: Portfolio & Risk Layer

**Responsibilities:**
- Portfolio optimization
- Risk monitoring and limits
- Position sizing
- Rebalancing

**Key Classes:**
- `PortfolioManager` - Main interface
- `PortfolioOptimizer` - Mean-Variance, Risk-Parity
- `RiskMonitor` - VaR, Drawdown, Concentration
- `PositionSizer` - Kelly, Volatility-based, Fixed-Fractional

```python
# Example: Portfolio optimization
optimal_weights = portfolio_manager.optimize_weights(
    returns=returns_data,
    method="mean_variance"  # or "risk_parity"
)

# Monitor risk
risk_metrics = portfolio_manager.get_risk_metrics(
    returns=returns_data,
    equity_curve=equity_curve
)

print(f"VaR (95%): {risk_metrics.var_95:.2%}")
print(f"Max Drawdown: {risk_metrics.max_drawdown:.2%}")
print(f"Leverage: {risk_metrics.current_leverage:.2f}x")
```

### Layer 4: Execution & Monitoring Layer

**Responsibilities:**
- Trade execution
- Live performance monitoring
- Model drift detection
- Error handling

**Key Classes:**
- `ExecutionManager` - Main interface
- `OrderExecutor` - Order placement and tracking
- `LiveMonitor` - Performance monitoring
- `DriftDetector` - Model drift detection

```python
# Example: Execute trade
order = execution_manager.execute_trade(
    symbol="AAPL",
    side="BUY",
    quantity=100,
    price=150.00
)

# Monitor performance
metrics = execution_manager.get_performance_metrics()
print(f"Win Rate: {metrics['win_rate']:.2%}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
print(f"Daily P&L: ${metrics['daily_pnl']:.2f}")

# Check for drift
is_drifting = execution_manager.check_for_drift(current_return=0.05)
```

### Layer 5: Orchestration Layer

**Responsibilities:**
- Workflow scheduling and execution
- Dependency management
- Error handling and retries
- Logging and monitoring

**Key Classes:**
- `OrchestrationManager` - Main interface
- `WorkflowExecutor` - Executes workflows
- `ScheduleManager` - Manages scheduling
- `WorkflowBuilder` - Builds workflows

```python
# Example: Create and schedule workflow
data_workflow = orchestration_manager.create_data_fetch_workflow(data_manager)
orchestration_manager.schedule_workflow(
    workflow=data_workflow,
    schedule_time="16:00",  # 4 PM UTC
    frequency="daily"
)

# Run workflow
result = await orchestration_manager.run_workflow(data_workflow)
```

---

## 🤖 Multi-Agent System

### Agent Communication

Agents communicate through a message-passing system:

```python
from src.agents import OracleAgent, AnalystAgent, SentinelAgent

# Initialize agents
oracle = OracleAgent(config={"vix_threshold": 20})
analyst = AnalystAgent(config={"min_confidence": 0.7})
sentinel = SentinelAgent(config={"max_leverage": 2.0})

# Oracle detects market regime
oracle_decision = oracle.process({
    "market_data": data,
    "vix": 18.5,
    "yield_curve": "normal"
})

# Analyst generates signals
analyst_decision = analyst.process({
    "signals": oracle_decision.recommendation,
    "returns_df": returns,
    "current_portfolio": portfolio
})

# Sentinel checks risk
sentinel_decision = sentinel.process({
    "proposed_trades": analyst_decision.recommendation,
    "current_portfolio": portfolio,
    "portfolio_value": 1000000
})
```

### Agent Roles

| Agent | Role | Responsibilities |
|-------|------|------------------|
| Oracle | Regime Detection | Market regime, macro signals |
| Analyst | Alpha Generation | Trading signals, clustering |
| Strategist | Portfolio Optimization | Weights, rebalancing |
| Sentinel | Risk Veto | Risk checks, compliance |
| Sovereign | Final Authority | Decision aggregation |

---

## 📈 3D Dashboard

The AEGIS-III system includes a sophisticated 3D React-Three-Fiber dashboard:

**Features:**
- Real-time agent status monitoring
- 3D cluster visualization (K-Means)
- Risk sphere (pulsating orb showing portfolio risk)
- Neural stream (live agent communication logs)
- Performance metrics
- Glassmorphism UI design

**Access:**
```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:3000
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_imports.py

# Run with coverage
pytest --cov=src

# Run specific layer tests
pytest tests/test_data_layer.py
pytest tests/test_research_layer.py
pytest tests/test_portfolio_layer.py
```

---

## 📊 MLflow Integration

Track experiments and compare strategies:

```bash
# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000

# View dashboard
# Open http://localhost:5000
```

All backtests automatically log to MLflow with:
- Strategy parameters
- Performance metrics (Sharpe, Return, Drawdown)
- Artifacts (charts, trade logs)

---

## 🔄 Workflow Examples

### Daily Trading Workflow

```
1. 16:00 UTC: Data Fetch
   ├─ Download market data
   ├─ Validate quality
   └─ Update cache

2. 09:30 UTC: Trade Execution
   ├─ Oracle: Detect regime
   ├─ Analyst: Generate signals
   ├─ Strategist: Optimize portfolio
   ├─ Sentinel: Risk check
   └─ Executor: Execute trades

3. 17:00 UTC: Monitoring
   ├─ Calculate daily P&L
   ├─ Check for drift
   └─ Log metrics
```

---

## 🛠️ Configuration

Edit `config/trading_config.ini`:

```ini
[STRATEGY]
ma_period = 20
threshold = 0.02

[RISK]
max_leverage = 2.0
var_limit = 0.02
max_drawdown = 0.20

[EXECUTION]
broker = interactive_brokers
account_id = YOUR_ACCOUNT_ID
```

---

## 📚 Documentation

- `RAVENSHIRE_ARCHITECTURE.md` - Detailed architecture documentation
- `VIDEO_ANALYSIS_IMPLEMENTATION.md` - Quant Science video analysis
- `RAVENSHIRE_ARCHITECTURE.md` - System design patterns

---

## 🚨 Risk Management

The system implements multiple layers of risk control:

1. **Position Sizing** - Kelly Criterion, Volatility-based
2. **Portfolio Limits** - Max leverage, concentration limits
3. **Risk Monitoring** - VaR, Drawdown, Correlation
4. **Drift Detection** - Model performance monitoring
5. **Veto Authority** - Sentinel agent can reject trades

---

## 🔐 Security

- API keys stored in environment variables
- No hardcoded credentials
- Data versioning for audit trail
- Comprehensive logging
- Error handling and recovery

---

## 📝 License

This project is proprietary. All rights reserved.

---

## 🤝 Contributing

Contributions welcome! Please follow:
1. Create feature branch
2. Write tests
3. Update documentation
4. Submit pull request

---

## 📧 Contact

For questions or support, contact the development team.

---

**Built with ❤️ by Ravenshire Capital**
