#!/usr/bin/env python
"""Simple test runner to verify setup"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test imports
try:
    from core.position import Position, PositionSide
    print("✓ core.position imported successfully")
    
    from core.portfolio import Portfolio
    print("✓ core.portfolio imported successfully")
    
    from core.trade import Trade, TradeType
    print("✓ core.trade imported successfully")
    
    from data.ohlc_pipeline import OHLCPipeline
    print("✓ data.ohlc_pipeline imported successfully")
    
    from data.fundamentals_pipeline import FundamentalsPipeline
    print("✓ data.fundamentals_pipeline imported successfully")
    
    from signals.signal_generator import SignalGenerator, Signal, SignalType
    print("✓ signals.signal_generator imported successfully")
    
    from signals.validator import SignalValidator
    print("✓ signals.validator imported successfully")
    
    from execution.executor import TradeExecutor, ExecutionResult
    print("✓ execution.executor imported successfully")
    
    from execution.order_manager import OrderManager
    print("✓ execution.order_manager imported successfully")
    
    from risk.risk_manager import RiskManager, RiskLimits
    print("✓ risk.risk_manager imported successfully")
    
    from risk.position_sizer import PositionSizer
    print("✓ risk.position_sizer imported successfully")
    
    from backtesting.backtest_engine import BacktestEngine
    print("✓ backtesting.backtest_engine imported successfully")
    
    from backtesting.walk_forward import WalkForwardValidator
    print("✓ backtesting.walk_forward imported successfully")
    
    from backtesting.permutation_test import PermutationTester
    print("✓ backtesting.permutation_test imported successfully")
    
    from watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory
    print("✓ watchlist.watchlist imported successfully")
    
    from watchlist.templates import populate_default_watchlists
    print("✓ watchlist.templates imported successfully")
    
    from watchlist.utils import print_watchlist_summary
    print("✓ watchlist.utils imported successfully")
    
    print("\n" + "="*50)
    print("✅ ALL MODULES IMPORTED SUCCESSFULLY!")
    print("="*50)
    
    # Run basic tests
    print("\nRunning basic functionality tests...\n")
    
    # Test 1: Position creation
    pos = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=150.0,
        entry_time=__import__("datetime").datetime.now(),
        side=PositionSide.LONG
    )
    assert pos.is_open == True
    print("✓ Position creation test passed")
    
    # Test 2: Position P&L
    pnl = pos.calculate_pnl(160.0)
    assert pnl == 1000.0
    print("✓ Position P&L calculation test passed")
    
    # Test 3: Portfolio creation
    portfolio = Portfolio(initial_capital=100000)
    assert portfolio.cash == 100000
    assert len(portfolio.positions) == 0
    print("✓ Portfolio creation test passed")
    
    # Test 4: Signal generation
    import pandas as pd
    gen = SignalGenerator()
    prices = pd.Series([100, 101, 102, 101, 99, 98, 100, 102])
    signal_type = gen.momentum_signal(prices, fast_period=2, slow_period=3)
    print(f"✓ Signal generation test passed (signal: {signal_type})")
    
    # Test 5: Risk manager
    limits = RiskLimits(max_position_size=0.1, max_leverage=2.0)
    risk_mgr = RiskManager(limits)
    is_valid, reason = risk_mgr.validate_trade(100000, 150000, 5000, -500)
    assert is_valid == True
    print(f"✓ Risk management test passed (valid: {is_valid})")
    
    # Test 6: Trade execution
    executor = TradeExecutor(slippage_bps=2.0, commission_pct=0.001)
    result = executor.execute_market_order("AAPL", 100, 150.0)
    assert result.quantity == 100
    assert result.commission > 0
    print(f"✓ Trade execution test passed (commission: ${result.commission:.2f})")
    
    # Test 7: Watchlist
    watchlist = Watchlist(name="Test Watchlist")
    watchlist.add_item(
        symbol="AAPL",
        name="Apple Inc.",
        asset_class=AssetClass.STOCK,
        category=WatchlistCategory.MOMENTUM,
        target_price=160.0,
        stop_loss=140.0
    )
    assert len(watchlist.get_all()) == 1
    watchlist.update_price("AAPL", 155.0)
    apple = watchlist.get_item("AAPL")
    assert apple.current_price == 155.0
    print(f"✓ Watchlist test passed (items: {len(watchlist.get_all())})")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    print("\nProject setup is complete and working correctly.")
    print("Run 'pytest tests/ -v' to execute the full test suite.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
