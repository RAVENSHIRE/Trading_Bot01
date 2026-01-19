"""Trade execution engine"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ExecutionStatus(Enum):
    """Execution status"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    symbol: str
    quantity: float
    price: float
    status: ExecutionStatus
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0


class TradeExecutor:
    """Execute trades with slippage and commission modeling"""
    
    def __init__(self, slippage_bps: float = 2.0, commission_pct: float = 0.001):
        self.slippage_bps = slippage_bps  # basis points
        self.commission_pct = commission_pct
        self.execution_history = []
    
    def execute_market_order(self, symbol: str, quantity: float,
                            current_price: float) -> ExecutionResult:
        """Execute market order with realistic slippage"""
        
        # Calculate slippage (in bps)
        slippage_amount = current_price * (self.slippage_bps / 10000)
        execution_price = current_price + slippage_amount
        
        # Calculate commission
        commission = quantity * execution_price * self.commission_pct
        
        result = ExecutionResult(
            symbol=symbol,
            quantity=quantity,
            price=execution_price,
            status=ExecutionStatus.FILLED,
            timestamp=datetime.now(),
            commission=commission,
            slippage=slippage_amount * quantity
        )
        
        self.execution_history.append(result)
        return result
    
    def execute_limit_order(self, symbol: str, quantity: float,
                           limit_price: float, current_price: float) -> Optional[ExecutionResult]:
        """Execute limit order if price conditions are met"""
        
        if current_price <= limit_price:
            return self.execute_market_order(symbol, quantity, limit_price)
        
        return ExecutionResult(
            symbol=symbol,
            quantity=0,
            price=0,
            status=ExecutionStatus.PENDING,
            timestamp=datetime.now()
        )


class OrderManager:
    """Manage active orders and order book"""
    
    def __init__(self):
        self.active_orders = {}
        self.filled_orders = []
    
    def create_market_order(self, symbol: str, quantity: float, 
                           side: str = "BUY") -> str:
        """Create market order"""
        order_id = f"{symbol}_{datetime.now().timestamp()}"
        self.active_orders[order_id] = {
            'symbol': symbol,
            'quantity': quantity,
            'side': side,
            'type': 'MARKET',
            'status': ExecutionStatus.PENDING
        }
        return order_id
    
    def create_limit_order(self, symbol: str, quantity: float,
                          limit_price: float, side: str = "BUY") -> str:
        """Create limit order"""
        order_id = f"{symbol}_{datetime.now().timestamp()}"
        self.active_orders[order_id] = {
            'symbol': symbol,
            'quantity': quantity,
            'price': limit_price,
            'side': side,
            'type': 'LIMIT',
            'status': ExecutionStatus.PENDING
        }
        return order_id
    
    def fill_order(self, order_id: str, filled_quantity: float, 
                  filled_price: float):
        """Fill an order"""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order['filled_quantity'] = filled_quantity
            order['filled_price'] = filled_price
            order['status'] = ExecutionStatus.FILLED
            self.filled_orders.append(order)
            del self.active_orders[order_id]
    
    def cancel_order(self, order_id: str):
        """Cancel an order"""
        if order_id in self.active_orders:
            self.active_orders[order_id]['status'] = ExecutionStatus.CANCELLED
            del self.active_orders[order_id]
