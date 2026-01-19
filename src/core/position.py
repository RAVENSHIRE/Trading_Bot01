"""Position tracking and management"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class PositionSide(Enum):
    """Position side enum"""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


@dataclass
class Position:
    """Represents a trading position"""
    
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    side: PositionSide
    
    def __post_init__(self):
        if self.quantity == 0:
            self.side = PositionSide.FLAT
    
    @property
    def is_open(self) -> bool:
        """Check if position is open"""
        return self.quantity != 0
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if self.side == PositionSide.LONG:
            return (current_price - self.entry_price) * self.quantity
        elif self.side == PositionSide.SHORT:
            return (self.entry_price - current_price) * abs(self.quantity)
        return 0.0
    
    def close(self, exit_price: float, exit_time: datetime) -> float:
        """Close position and return realized P&L"""
        realized_pnl = self.calculate_pnl(exit_price)
        self.quantity = 0
        self.side = PositionSide.FLAT
        return realized_pnl
