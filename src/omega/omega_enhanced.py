"""
OMEGA Trading System - Enhanced Version
Complete implementation with detailed logging, risk management, and portfolio analytics
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
from tabulate import tabulate
import numpy as np

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    symbol: str
    quantity: float
    order_type: OrderType
    side: str
    price: Optional[float] = None
    stop_price: Optional[float] = None
    target_percentage: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    order_id: Optional[str] = None
    execution_time: Optional[float] = None
    
    def __str__(self):
        return f"{self.side} {self.quantity:.2f} {self.symbol} @ {self.order_type.value} ({self.status.value})"


@dataclass
class Position:
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    last_update: datetime = field(default_factory=datetime.now)
    
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
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    orders: List[Order] = field(default_factory=list)
    trades_log: List[Dict] = field(default_factory=list)
    daily_trades: List[Dict] = field(default_factory=list)
    
    @property
    def total_value(self) -> float:
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def portfolio_allocation(self) -> Dict[str, float]:
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
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def daily_pnl_pct(self) -> float:
        if self.total_value == 0:
            return 0.0
        return (self.daily_pnl / self.total_value) * 100
    
    @property
    def total_trades_today(self) -> int:
        return len(self.daily_trades)
    
    @property
    def total_volume_today(self) -> float:
        return sum(trade.get('quantity', 0) for trade in self.daily_trades)


class RiskEngine:
    """Advanced Risk Management"""
    
    def __init__(self, max_position_size_pct: float = 0.1, max_leverage: float = 2.0, var_confidence: float = 0.95):
        self.max_position_size_pct = max_position_size_pct
        self.max_leverage = max_leverage
        self.var_confidence = var_confidence
        self.risk_metrics = {}
    
    def calculate_var(self, portfolio: Portfolio, returns: List[float]) -> float:
        """Calculate Value at Risk"""
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * (1 - self.var_confidence))
        return sorted_returns[var_index] * portfolio.total_value
    
    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not portfolio_values:
            return 0.0
        max_val = portfolio_values[0]
        max_dd = 0.0
        for val in portfolio_values:
            if val > max_val:
                max_val = val
            dd = (max_val - val) / max_val
            if dd > max_dd:
                max_dd = dd
        return max_dd * 100
    
    def check_margin_requirement(self, portfolio: Portfolio, order: Order) -> Tuple[bool, str]:
        if order.side == "BUY":
            required_cash = order.quantity * (order.price or 100)
            if required_cash > portfolio.cash:
                return False, f"❌ Insufficient cash. Required: ${required_cash:,.2f}, Available: ${portfolio.cash:,.2f}"
        return True, "✅ Margin check passed"
    
    def check_position_size(self, portfolio: Portfolio, order: Order) -> Tuple[bool, str]:
        if order.price is None:
            return True, "✅ Position size check skipped"
        
        order_value = order.quantity * order.price
        max_position_value = portfolio.total_value * self.max_position_size_pct
        
        if order_value > max_position_value:
            return False, f"❌ Position exceeds limit. Max: ${max_position_value:,.2f}, Requested: ${order_value:,.2f}"
        return True, "✅ Position size check passed"
    
    def generate_risk_alerts(self, portfolio: Portfolio) -> List[str]:
        alerts = []
        
        if portfolio.daily_pnl_pct < -5.0:
            alerts.append(f"🚨 ALERT: Daily loss exceeds -5%: {portfolio.daily_pnl_pct:.2f}%")
        
        allocation = portfolio.portfolio_allocation
        for symbol, pct in allocation.items():
            if pct > 30 and symbol != 'CASH':
                alerts.append(f"⚠️ WARNING: High concentration in {symbol}: {pct:.1f}%")
        
        total_positions = sum(pos.market_value for pos in portfolio.positions.values())
        leverage = total_positions / portfolio.total_value if portfolio.total_value > 0 else 0
        if leverage > 1.5:
            alerts.append(f"⚠️ WARNING: High leverage: {leverage:.2f}x")
        
        return alerts


class OMEGATradingEngine:
    """OMEGA Trading System - Main Engine"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.portfolio = Portfolio(cash=initial_capital)
        self.risk_engine = RiskEngine()
        self.market_data: Dict[str, Dict] = {}
        self.portfolio_history: List[float] = [initial_capital]
        self.order_counter = 0
        
        logger.info(f"{'='*80}")
        logger.info(f"OMEGA TRADING SYSTEM - INITIALIZED")
        logger.info(f"{'='*80}")
        logger.info(f"Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"{'='*80}\n")
    
    def update_market_data(self, symbol: str, price: float) -> None:
        """Update market data for a symbol"""
        self.market_data[symbol] = {
            'price': price,
            'timestamp': datetime.now()
        }
    
    def submit_order(self, order: Order) -> Tuple[bool, str]:
        """Submit order with risk checks"""
        logger.info(f"\n{'='*80}")
        logger.info(f"ORDER SUBMISSION: {order}")
        logger.info(f"{'='*80}")
        
        # Risk checks
        checks = [
            self.risk_engine.check_margin_requirement(self.portfolio, order),
            self.risk_engine.check_position_size(self.portfolio, order),
        ]
        
        for passed, message in checks:
            logger.info(message)
            if not passed:
                order.status = OrderStatus.REJECTED
                logger.error(f"❌ ORDER REJECTED\n")
                return False, message
        
        self.order_counter += 1
        order.order_id = f"ORD-{self.order_counter:06d}"
        order.status = OrderStatus.SUBMITTED
        self.portfolio.orders.append(order)
        
        logger.info(f"✅ ORDER SUBMITTED: {order.order_id}\n")
        return True, "Order submitted successfully"
    
    def execute_order(self, order: Order, execution_price: float) -> bool:
        """Execute order"""
        logger.info(f"\n{'='*80}")
        logger.info(f"ORDER EXECUTION: {order.order_id}")
        logger.info(f"{'='*80}")
        logger.info(f"Symbol: {order.symbol}")
        logger.info(f"Side: {order.side}")
        logger.info(f"Quantity: {order.quantity:.2f}")
        logger.info(f"Execution Price: ${execution_price:.2f}")
        logger.info(f"Order Type: {order.order_type.value}")
        
        execution_start = datetime.now()
        
        if order.side == "BUY":
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
            
            self.portfolio.cash -= execution_price * order.quantity
            logger.info(f"✅ BUY EXECUTED: {order.quantity:.2f} {order.symbol} @ ${execution_price:.2f}")
        
        elif order.side == "SELL":
            if order.symbol in self.portfolio.positions:
                pos = self.portfolio.positions[order.symbol]
                pos.quantity -= order.quantity
                if pos.quantity <= 0:
                    del self.portfolio.positions[order.symbol]
            
            self.portfolio.cash += execution_price * order.quantity
            logger.info(f"✅ SELL EXECUTED: {order.quantity:.2f} {order.symbol} @ ${execution_price:.2f}")
        
        # Log trade
        trade_log = {
            'timestamp': datetime.now(),
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'price': execution_price,
            'order_id': order.order_id,
            'order_type': order.order_type.value,
            'total_value': execution_price * order.quantity
        }
        self.portfolio.trades_log.append(trade_log)
        self.portfolio.daily_trades.append(trade_log)
        
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_price = execution_price
        order.execution_time = (datetime.now() - execution_start).total_seconds()
        
        logger.info(f"Execution Time: {order.execution_time:.3f}s")
        logger.info(f"Portfolio Value: ${self.portfolio.total_value:,.2f}")
        logger.info(f"Cash: ${self.portfolio.cash:,.2f}\n")
        
        return True
    
    def rebalance_portfolio(self, target_allocation: Dict[str, float]) -> List[Order]:
        """Rebalance portfolio to target allocation"""
        logger.info(f"\n{'='*80}")
        logger.info(f"PORTFOLIO REBALANCING")
        logger.info(f"{'='*80}")
        
        orders = []
        current_allocation = self.portfolio.portfolio_allocation
        
        logger.info(f"\nCurrent Allocation:")
        for symbol, pct in current_allocation.items():
            logger.info(f"  {symbol}: {pct:.2f}%")
        
        logger.info(f"\nTarget Allocation:")
        for symbol, pct in target_allocation.items():
            logger.info(f"  {symbol}: {pct:.2f}%")
        
        for symbol, target_pct in target_allocation.items():
            current_pct = current_allocation.get(symbol, 0)
            diff_pct = target_pct - current_pct
            
            if abs(diff_pct) > 0.5:
                target_value = self.portfolio.total_value * (target_pct / 100)
                current_value = self.portfolio.positions.get(symbol, Position(symbol, 0, 0, 0)).market_value
                diff_value = target_value - current_value
                
                if diff_value > 0:
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
                    logger.info(f"  ➜ BUY {quantity:.2f} {symbol} (Rebalance)")
                
                elif diff_value < 0:
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
                    logger.info(f"  ➜ SELL {quantity:.2f} {symbol} (Rebalance)")
        
        logger.info(f"\nGenerated {len(orders)} rebalancing orders\n")
        return orders
    
    def print_portfolio_summary(self) -> None:
        """Print detailed portfolio summary"""
        logger.info(f"\n{'='*80}")
        logger.info(f"PORTFOLIO SUMMARY")
        logger.info(f"{'='*80}\n")
        
        # Portfolio metrics
        logger.info(f"Total Portfolio Value: ${self.portfolio.total_value:,.2f}")
        logger.info(f"Cash Balance: ${self.portfolio.cash:,.2f}")
        logger.info(f"Positions Value: ${self.portfolio.total_value - self.portfolio.cash:,.2f}")
        logger.info(f"Daily P&L: ${self.portfolio.daily_pnl:,.2f} ({self.portfolio.daily_pnl_pct:.2f}%)")
        logger.info(f"Total Trades Today: {self.portfolio.total_trades_today}")
        logger.info(f"Total Volume Today: ${self.portfolio.total_volume_today:,.2f}\n")
        
        # Positions table
        if self.portfolio.positions:
            logger.info(f"OPEN POSITIONS:")
            positions_data = []
            for symbol, pos in self.portfolio.positions.items():
                positions_data.append([
                    symbol,
                    f"{pos.quantity:.2f}",
                    f"${pos.average_cost:.2f}",
                    f"${pos.current_price:.2f}",
                    f"${pos.market_value:,.2f}",
                    f"${pos.unrealized_pnl:,.2f}",
                    f"{pos.unrealized_pnl_pct:.2f}%"
                ])
            
            headers = ["Symbol", "Qty", "Avg Cost", "Current", "Value", "P&L", "P&L %"]
            logger.info(tabulate(positions_data, headers=headers, tablefmt="grid"))
        
        # Allocation
        logger.info(f"\nPORTFOLIO ALLOCATION:")
        allocation_data = []
        for symbol, pct in self.portfolio.portfolio_allocation.items():
            allocation_data.append([symbol, f"{pct:.2f}%"])
        logger.info(tabulate(allocation_data, headers=["Symbol", "Allocation"], tablefmt="grid"))
        
        # Risk alerts
        alerts = self.risk_engine.generate_risk_alerts(self.portfolio)
        if alerts:
            logger.info(f"\nRISK ALERTS:")
            for alert in alerts:
                logger.warning(alert)
        else:
            logger.info(f"\n✅ No risk alerts")
        
        logger.info(f"\n{'='*80}\n")
    
    def print_trade_log(self) -> None:
        """Print trade execution log"""
        if not self.portfolio.daily_trades:
            logger.info("No trades executed today")
            return
        
        logger.info(f"\n{'='*80}")
        logger.info(f"TRADE EXECUTION LOG")
        logger.info(f"{'='*80}\n")
        
        trades_data = []
        for trade in self.portfolio.daily_trades:
            trades_data.append([
                trade['timestamp'].strftime("%H:%M:%S"),
                trade['order_id'],
                trade['side'],
                trade['symbol'],
                f"{trade['quantity']:.2f}",
                f"${trade['price']:.2f}",
                f"${trade['total_value']:,.2f}",
                trade['order_type']
            ])
        
        headers = ["Time", "Order ID", "Side", "Symbol", "Qty", "Price", "Total", "Type"]
        logger.info(tabulate(trades_data, headers=headers, tablefmt="grid"))
        logger.info(f"\n{'='*80}\n")


# Example usage
if __name__ == "__main__":
    engine = OMEGATradingEngine(initial_capital=100000)
    
    # Update market data
    engine.update_market_data('AAPL', 150.0)
    engine.update_market_data('MSFT', 300.0)
    engine.update_market_data('GOOGL', 140.0)
    
    # Create and execute orders
    orders = [
        Order(symbol='AAPL', quantity=10, order_type=OrderType.MARKET, side='BUY', price=150.0),
        Order(symbol='MSFT', quantity=5, order_type=OrderType.MARKET, side='BUY', price=300.0),
        Order(symbol='GOOGL', quantity=8, order_type=OrderType.MARKET, side='BUY', price=140.0),
    ]
    
    for order in orders:
        success, msg = engine.submit_order(order)
        if success:
            engine.execute_order(order, order.price)
    
    # Rebalance
    target_allocation = {'AAPL': 40, 'MSFT': 30, 'GOOGL': 20, 'CASH': 10}
    rebalance_orders = engine.rebalance_portfolio(target_allocation)
    
    # Print summaries
    engine.print_portfolio_summary()
    engine.print_trade_log()
