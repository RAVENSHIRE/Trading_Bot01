"""Trade record and execution tracking"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class TradeType(Enum):
    """Trade type enum"""
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class OrderStatus(Enum):
    """Order status enum"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Trade:
    """Represents a single trade"""
    
    symbol: str
    trade_type: TradeType
    quantity: float
    price: float
    timestamp: datetime
    order_id: str
    status: OrderStatus = OrderStatus.PENDING
    commission: float = 0.0
    slippage: float = 0.0
    
    def execute(self, execution_price: float, execution_qty: float):
        """Execute the trade"""
        self.price = execution_price
        self.quantity = execution_qty
        self.status = OrderStatus.FILLED
    
    @property
    def total_value(self) -> float:
        """Get total trade value"""
        return self.quantity * self.price
    
    @property
    def net_cost(self) -> float:
        """Get net cost including commission and slippage"""
        return self.total_value + self.commission + self.slippage
