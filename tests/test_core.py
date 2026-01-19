"""Basic tests for core modules"""

import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.position import Position, PositionSide
from core.portfolio import Portfolio
from datetime import datetime


def test_position_creation():
    """Test position creation"""
    pos = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=150.0,
        entry_time=datetime.now(),
        side=PositionSide.LONG
    )
    assert pos.is_open is True
    assert pos.symbol == "AAPL"


def test_position_pnl():
    """Test position P&L calculation"""
    pos = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=150.0,
        entry_time=datetime.now(),
        side=PositionSide.LONG
    )
    
    pnl = pos.calculate_pnl(160.0)
    assert pnl == 1000.0  # 100 * (160 - 150)


def test_portfolio_creation():
    """Test portfolio creation"""
    portfolio = Portfolio(initial_capital=100000)
    assert portfolio.cash == 100000
    assert len(portfolio.positions) == 0


def test_portfolio_nav():
    """Test portfolio NAV calculation"""
    portfolio = Portfolio(initial_capital=100000)
    
    pos = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=150.0,
        entry_time=datetime.now(),
        side=PositionSide.LONG
    )
    portfolio.add_position(pos)
    
    nav = portfolio.get_nav({"AAPL": 160.0})
    assert nav > 100000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
