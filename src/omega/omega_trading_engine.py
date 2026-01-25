"""
OMEGA Trading System - A Hedge Fund in a Box
Automated Portfolio Rebalancing, Trade Execution, Risk Management, and Logging
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by OMEGA"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """Trade order representation"""
    symbol: str
    quantity: float
    order_type: OrderType
    side: str  # "BUY" or "SELL"
    price: Optional[float] = None
    stop_price: Optional[float] = None
    target_percentage: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    order_id: Optional[str] = None


@dataclass
class Position:
    """Portfolio position"""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.average_cost) * self.quantity
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.average_cost == 0:
            return 0.0
        return (self.unrealized_pnl / (self.average_cost * self.quantity)) * 100


@dataclass
class Portfolio:
    """Portfolio state"""
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    orders: List[Order] = field(default_factory=list)
    trades_log: List[Dict] = field(default_factory=list)
    
    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def portfolio_allocation(self) -> Dict[str, float]:
        """Current portfolio allocation percentages"""
        total = self.total_value
        if total == 0:
            return {}
        
        allocation = {}
        for symbol, position in self.positions.items():
            allocation[symbol] = (position.market_value / total) * 100
        allocation['CASH'] = (self.cash / total) * 100
        return allocation
    
    @property
    def daily_pnl(self) -> float:
        """Daily profit and loss"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def daily_pnl_pct(self) -> float:
        """Daily P&L percentage"""
        if self.total_value == 0:
            return 0.0
        return (self.daily_pnl / self.total_value) * 100


class RiskEngine:
    """Risk Management Engine"""
    
    def __init__(self, max_position_size_pct: float = 0.1, max_leverage: float = 2.0):
        self.max_position_size_pct = max_position_size_pct
        self.max_leverage = max_leverage
    
    def check_margin_requirement(self, portfolio: Portfolio, order: Order) -> Tuple[bool, str]:
        """Check if order meets margin requirements"""
        if order.side == "BUY":
            required_cash = order.quantity * order.price if order.price else 0
            if required_cash > portfolio.cash:
                return False, f"Insufficient cash. Required: {required_cash}, Available: {portfolio.cash}"
        return True, "Margin check passed"
    
    def check_position_size(self, portfolio: Portfolio, order: Order) -> Tuple[bool, str]:
        """Check if order exceeds maximum position size"""
        if order.price is None:
            return True, "Position size check skipped (no price)"
        
        order_value = order.quantity * order.price
        max_position_value = portfolio.total_value * self.max_position_size_pct
        
        if order_value > max_position_value:
            return False, f"Position size exceeds limit. Max: {max_position_value}, Requested: {order_value}"
        return True, "Position size check passed"
    
    def check_leverage(self, portfolio: Portfolio) -> Tuple[bool, str]:
        """Check if portfolio leverage is within limits"""
        total_positions = sum(pos.market_value for pos in portfolio.positions.values())
        leverage = total_positions / portfolio.total_value if portfolio.total_value > 0 else 0
        
        if leverage > self.max_leverage:
            return False, f"Leverage exceeds limit. Current: {leverage:.2f}x, Max: {self.max_leverage}x"
        return True, "Leverage check passed"
    
    def generate_risk_alerts(self, portfolio: Portfolio) -> List[str]:
        """Generate risk alerts based on portfolio metrics"""
        alerts = []
        
        # Check daily loss threshold
        if portfolio.daily_pnl_pct < -5.0:
            alerts.append(f"⚠️ Daily loss exceeds -5%: {portfolio.daily_pnl_pct:.2f}%")
        
        # Check position concentration
        allocation = portfolio.portfolio_allocation
        for symbol, pct in allocation.items():
            if pct > 30 and symbol != 'CASH':
                alerts.append(f"⚠️ Position concentration: {symbol} = {pct:.1f}%")
        
        # Check leverage
        total_positions = sum(pos.market_value for pos in portfolio.positions.values())
        leverage = total_positions / portfolio.total_value if portfolio.total_value > 0 else 0
        if leverage > 1.5:
            alerts.append(f"⚠️ High leverage: {leverage:.2f}x")
        
        return alerts


class OMEGATradingEngine:
    """Main OMEGA Trading Engine"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.portfolio = Portfolio(cash=initial_capital)
        self.risk_engine = RiskEngine()
        self.market_data: Dict[str, Dict] = {}
        logger.info(f"OMEGA Trading Engine initialized with ${initial_capital:,.2f}")
    
    async def stream_market_data(self, symbols: List[str]) -> None:
        """Stream real-time market data"""
        logger.info(f"Streaming market data for: {symbols}")
        # This would connect to Swissquote/OpenWealth API
        # For now, simulate with random data
        pass
    
    def submit_order(self, order: Order) -> Tuple[bool, str]:
        """Submit an order with risk checks"""
        logger.info(f"Submitting order: {order.side} {order.quantity} {order.symbol} @ {order.order_type}")
        
        # Risk checks
        checks = [
            self.risk_engine.check_margin_requirement(self.portfolio, order),
            self.risk_engine.check_position_size(self.portfolio, order),
        ]
        
        for passed, message in checks:
            if not passed:
                logger.error(f"Order rejected: {message}")
                order.status = OrderStatus.REJECTED
                return False, message
        
        order.status = OrderStatus.SUBMITTED
        self.portfolio.orders.append(order)
        logger.info(f"Order submitted: {order.order_id}")
        return True, "Order submitted successfully"
    
    def execute_order(self, order: Order, execution_price: float) -> bool:
        """Execute an order at given price"""
        logger.info(f"Executing order {order.order_id}: {order.quantity} {order.symbol} @ {execution_price}")
        
        if order.side == "BUY":
            # Update position
            if order.symbol in self.portfolio.positions:
                pos = self.portfolio.positions[order.symbol]
                total_cost = pos.average_cost * pos.quantity + execution_price * order.quantity
                pos.quantity += order.quantity
                pos.average_cost = total_cost / pos.quantity
            else:
                self.portfolio.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_cost=execution_price,
                    current_price=execution_price
                )
            
            # Update cash
            self.portfolio.cash -= execution_price * order.quantity
        
        elif order.side == "SELL":
            if order.symbol in self.portfolio.positions:
                pos = self.portfolio.positions[order.symbol]
                pos.quantity -= order.quantity
                if pos.quantity <= 0:
                    del self.portfolio.positions[order.symbol]
            
            # Update cash
            self.portfolio.cash += execution_price * order.quantity
        
        # Log trade
        self.portfolio.trades_log.append({
            'timestamp': datetime.now(),
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'price': execution_price,
            'order_id': order.order_id
        })
        
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_price = execution_price
        logger.info(f"Order executed: {order.order_id}")
        return True
    
    def rebalance_portfolio(self, target_allocation: Dict[str, float]) -> List[Order]:
        """Rebalance portfolio to target allocation"""
        logger.info(f"Rebalancing portfolio to target: {target_allocation}")
        
        orders = []
        current_allocation = self.portfolio.portfolio_allocation
        
        for symbol, target_pct in target_allocation.items():
            current_pct = current_allocation.get(symbol, 0)
            diff_pct = target_pct - current_pct
            
            if abs(diff_pct) > 0.5:  # Only rebalance if difference > 0.5%
                target_value = self.portfolio.total_value * (target_pct / 100)
                current_value = self.portfolio.positions.get(symbol, Position(symbol, 0, 0, 0)).market_value
                diff_value = target_value - current_value
                
                if diff_value > 0:
                    # Buy
                    current_price = self.market_data.get(symbol, {}).get('price', 100)
                    quantity = diff_value / current_price
                    order = Order(
                        symbol=symbol,
                        quantity=quantity,
                        order_type=OrderType.MARKET,
                        side="BUY",
                        price=current_price,
                        target_percentage=target_pct
                    )
                    orders.append(order)
                elif diff_value < 0:
                    # Sell
                    current_price = self.market_data.get(symbol, {}).get('price', 100)
                    quantity = abs(diff_value) / current_price
                    order = Order(
                        symbol=symbol,
                        quantity=quantity,
                        order_type=OrderType.MARKET,
                        side="SELL",
                        price=current_price,
                        target_percentage=target_pct
                    )
                    orders.append(order)
        
        logger.info(f"Generated {len(orders)} rebalancing orders")
        return orders
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        return {
            'total_value': self.portfolio.total_value,
            'cash': self.portfolio.cash,
            'positions': len(self.portfolio.positions),
            'daily_pnl': self.portfolio.daily_pnl,
            'daily_pnl_pct': self.portfolio.daily_pnl_pct,
            'allocation': self.portfolio.portfolio_allocation,
            'risk_alerts': self.risk_engine.generate_risk_alerts(self.portfolio)
        }
    
    def get_trade_log(self) -> List[Dict]:
        """Get trade execution log"""
        return self.portfolio.trades_log


# Example usage
if __name__ == "__main__":
    engine = OMEGATradingEngine(initial_capital=100000)
    
    # Simulate market data
    engine.market_data = {
        'AAPL': {'price': 150.0},
        'MSFT': {'price': 300.0},
        'GOOGL': {'price': 140.0},
    }
    
    # Create and execute a buy order
    order = Order(
        symbol='AAPL',
        quantity=10,
        order_type=OrderType.MARKET,
        side='BUY',
        price=150.0
    )
    
    success, message = engine.submit_order(order)
    if success:
        engine.execute_order(order, 150.0)
    
    # Print portfolio summary
    summary = engine.get_portfolio_summary()
    print("\n=== OMEGA Trading Engine Summary ===")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Cash: ${summary['cash']:,.2f}")
    print(f"Daily P&L: ${summary['daily_pnl']:,.2f} ({summary['daily_pnl_pct']:.2f}%)")
    print(f"Positions: {summary['positions']}")
    print(f"Allocation: {summary['allocation']}")
    if summary['risk_alerts']:
        print(f"Risk Alerts: {summary['risk_alerts']}")
