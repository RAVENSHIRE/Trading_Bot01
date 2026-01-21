"""
Execution and Monitoring Layer - Trade execution and live monitoring
Part of the 5-Layer Hedge Fund Architecture
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """Represents a trading order"""
    order_id: str
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float
    order_type: str  # MARKET, LIMIT, STOP
    status: str  # PENDING, FILLED, CANCELLED, REJECTED
    created_at: str
    filled_at: Optional[str] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "order_type": self.order_type,
            "status": self.status,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "filled_price": self.filled_price,
            "filled_quantity": self.filled_quantity
        }


@dataclass
class Trade:
    """Represents a completed trade"""
    trade_id: str
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: Optional[str]
    exit_price: Optional[float]
    quantity: float
    pnl: float
    pnl_pct: float
    status: str  # OPEN, CLOSED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "entry_date": self.entry_date,
            "entry_price": self.entry_price,
            "exit_date": self.exit_date,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "status": self.status
        }


class OrderExecutor:
    """Executes orders"""
    
    def __init__(self, broker_api=None):
        self.broker_api = broker_api
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_type: str = "MARKET"
    ) -> Order:
        """
        Place an order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            price: Order price
            order_type: MARKET, LIMIT, STOP
            
        Returns:
            Order object
        """
        # Generate order ID
        self.order_counter += 1
        order_id = f"ORD_{self.order_counter}_{datetime.utcnow().timestamp()}"
        
        # Create order
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            status="PENDING",
            created_at=str(datetime.utcnow())
        )
        
        # Store order
        self.orders[order_id] = order
        
        logger.info(f"Order placed: {order_id} - {side} {quantity} {symbol} @ {price}")
        
        # Execute via broker API if available
        if self.broker_api:
            try:
                self._execute_with_broker(order)
            except Exception as e:
                logger.error(f"Broker execution failed: {e}")
                order.status = "REJECTED"
        else:
            # Simulate execution
            order.status = "FILLED"
            order.filled_at = str(datetime.utcnow())
            order.filled_price = price
            order.filled_quantity = quantity
        
        return order
    
    def _execute_with_broker(self, order: Order) -> None:
        """Execute order with broker API"""
        # This would call the actual broker API
        # For now, just simulate
        order.status = "FILLED"
        order.filled_at = str(datetime.utcnow())
        order.filled_price = order.price
        order.filled_quantity = order.quantity
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        order = self.orders[order_id]
        
        if order.status in ["FILLED", "CANCELLED"]:
            logger.warning(f"Cannot cancel order with status: {order.status}")
            return False
        
        order.status = "CANCELLED"
        logger.info(f"Order cancelled: {order_id}")
        return True
    
    def get_order_status(self, order_id: str) -> Optional[str]:
        """Get order status"""
        if order_id in self.orders:
            return self.orders[order_id].status
        return None
    
    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        return [o for o in self.orders.values() if o.status == "PENDING"]
    
    def get_filled_orders(self) -> List[Order]:
        """Get all filled orders"""
        return [o for o in self.orders.values() if o.status == "FILLED"]


class LiveMonitor:
    """Monitors live trading performance"""
    
    def __init__(self):
        self.trades: Dict[str, Trade] = {}
        self.trade_counter = 0
        self.daily_pnl = 0
        self.realized_pnl = 0
        self.unrealized_pnl = 0
    
    def create_trade(
        self,
        symbol: str,
        quantity: float,
        entry_price: float
    ) -> Trade:
        """Create a new trade"""
        self.trade_counter += 1
        trade_id = f"TRD_{self.trade_counter}"
        
        trade = Trade(
            trade_id=trade_id,
            symbol=symbol,
            entry_date=str(datetime.utcnow().date()),
            entry_price=entry_price,
            exit_date=None,
            exit_price=None,
            quantity=quantity,
            pnl=0,
            pnl_pct=0,
            status="OPEN"
        )
        
        self.trades[trade_id] = trade
        logger.info(f"Trade created: {trade_id} - {quantity} {symbol} @ {entry_price}")
        
        return trade
    
    def close_trade(
        self,
        trade_id: str,
        exit_price: float
    ) -> Optional[Trade]:
        """Close a trade"""
        if trade_id not in self.trades:
            logger.warning(f"Trade not found: {trade_id}")
            return None
        
        trade = self.trades[trade_id]
        
        if trade.status == "CLOSED":
            logger.warning(f"Trade already closed: {trade_id}")
            return trade
        
        # Calculate P&L
        trade.exit_date = str(datetime.utcnow().date())
        trade.exit_price = exit_price
        trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        trade.pnl_pct = (exit_price - trade.entry_price) / trade.entry_price
        trade.status = "CLOSED"
        
        # Update realized P&L
        self.realized_pnl += trade.pnl
        
        logger.info(f"Trade closed: {trade_id} - P&L: {trade.pnl:.2f} ({trade.pnl_pct:.2%})")
        
        return trade
    
    def get_open_trades(self) -> List[Trade]:
        """Get all open trades"""
        return [t for t in self.trades.values() if t.status == "OPEN"]
    
    def get_closed_trades(self) -> List[Trade]:
        """Get all closed trades"""
        return [t for t in self.trades.values() if t.status == "CLOSED"]
    
    def calculate_daily_pnl(self, current_prices: Dict[str, float]) -> float:
        """Calculate daily P&L"""
        self.unrealized_pnl = 0
        
        for trade in self.get_open_trades():
            if trade.symbol in current_prices:
                current_price = current_prices[trade.symbol]
                unrealized = (current_price - trade.entry_price) * trade.quantity
                self.unrealized_pnl += unrealized
        
        self.daily_pnl = self.realized_pnl + self.unrealized_pnl
        return self.daily_pnl
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        closed_trades = self.get_closed_trades()
        
        if len(closed_trades) == 0:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
                "realized_pnl": self.realized_pnl,
                "unrealized_pnl": self.unrealized_pnl,
                "daily_pnl": self.daily_pnl
            }
        
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]
        
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        
        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed_trades),
            "avg_win": total_wins / len(winning_trades) if winning_trades else 0,
            "avg_loss": total_losses / len(losing_trades) if losing_trades else 0,
            "profit_factor": total_wins / total_losses if total_losses > 0 else 0,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "daily_pnl": self.daily_pnl
        }


class DriftDetector:
    """Detects model drift"""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.historical_returns = []
        self.drift_threshold = 2.0  # Standard deviations
    
    def check_drift(self, current_return: float, baseline_mean: float, baseline_std: float) -> bool:
        """
        Check if current return indicates drift
        
        Args:
            current_return: Current return
            baseline_mean: Historical mean return
            baseline_std: Historical std of returns
            
        Returns:
            True if drift detected
        """
        if baseline_std == 0:
            return False
        
        z_score = abs((current_return - baseline_mean) / baseline_std)
        
        if z_score > self.drift_threshold:
            logger.warning(f"Drift detected! Z-score: {z_score:.2f}")
            return True
        
        return False
    
    def add_return(self, return_value: float) -> None:
        """Add return to history"""
        self.historical_returns.append(return_value)
        
        # Keep only recent returns
        if len(self.historical_returns) > self.window_size * 2:
            self.historical_returns = self.historical_returns[-self.window_size * 2:]
    
    def get_baseline_stats(self) -> tuple:
        """Get baseline statistics"""
        if len(self.historical_returns) < self.window_size:
            return 0, 1
        
        baseline = self.historical_returns[-self.window_size:]
        import numpy as np
        return np.mean(baseline), np.std(baseline)


class ExecutionManager:
    """Main execution interface"""
    
    def __init__(self):
        self.executor = OrderExecutor()
        self.monitor = LiveMonitor()
        self.drift_detector = DriftDetector()
    
    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Execute a trade"""
        return self.executor.place_order(symbol, side, quantity, price)
    
    def close_position(self, trade_id: str, exit_price: float) -> Optional[Trade]:
        """Close a position"""
        return self.monitor.close_trade(trade_id, exit_price)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.monitor.get_performance_metrics()
    
    def check_for_drift(self, current_return: float) -> bool:
        """Check for model drift"""
        baseline_mean, baseline_std = self.drift_detector.get_baseline_stats()
        return self.drift_detector.check_drift(current_return, baseline_mean, baseline_std)
