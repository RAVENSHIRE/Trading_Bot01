"""Portfolio management and P&L tracking"""

from datetime import datetime
from typing import Dict, List, Optional
from .position import Position, PositionSide
from .trade import Trade, TradeType


class Portfolio:
    """Main portfolio manager"""
    
    def __init__(self, initial_capital: float, name: str = "MainPortfolio"):
        self.name = name
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.realized_pnl = 0.0
        self.creation_time = datetime.now()
    
    def add_position(self, position: Position) -> None:
        """Add or update a position"""
        self.positions[position.symbol] = position
    
    def close_position(self, symbol: str, exit_price: float, exit_time: datetime) -> float:
        """Close a position"""
        if symbol not in self.positions:
            raise ValueError(f"Position {symbol} not found")
        
        position = self.positions[symbol]
        realized_pnl = position.close(exit_price, exit_time)
        self.realized_pnl += realized_pnl
        return realized_pnl
    
    def record_trade(self, trade: Trade) -> None:
        """Record a trade"""
        self.trade_history.append(trade)
        if trade.trade_type == TradeType.ENTRY:
            self.cash -= trade.net_cost
        else:
            self.cash += trade.net_cost
    
    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """Calculate total unrealized P&L"""
        unrealized = 0.0
        for symbol, position in self.positions.items():
            if symbol in current_prices and position.is_open:
                unrealized += position.calculate_pnl(current_prices[symbol])
        return unrealized
    
    def get_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """Get total P&L (realized + unrealized)"""
        return self.realized_pnl + self.get_unrealized_pnl(current_prices)
    
    def get_nav(self, current_prices: Dict[str, float]) -> float:
        """Get net asset value"""
        position_value = sum(
            pos.quantity * current_prices.get(symbol, 0)
            for symbol, pos in self.positions.items()
        )
        return self.cash + position_value
    
    def get_leverage(self, current_prices: Dict[str, float]) -> float:
        """Calculate current leverage"""
        nav = self.get_nav(current_prices)
        if nav <= 0:
            return 0.0
        
        gross_exposure = sum(
            abs(pos.quantity * current_prices.get(symbol, 0))
            for symbol, pos in self.positions.items()
        )
        return gross_exposure / nav
    
    def get_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get portfolio summary"""
        nav = self.get_nav(current_prices)
        total_pnl = self.get_total_pnl(current_prices)
        
        return {
            "name": self.name,
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "nav": nav,
            "return_pct": (nav - self.initial_capital) / self.initial_capital * 100,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.get_unrealized_pnl(current_prices),
            "total_pnl": total_pnl,
            "leverage": self.get_leverage(current_prices),
            "num_trades": len(self.trade_history),
            "open_positions": len([p for p in self.positions.values() if p.is_open]),
        }
