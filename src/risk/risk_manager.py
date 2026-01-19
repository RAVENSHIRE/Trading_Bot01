"""Risk management and controls"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class RiskLimits:
    """Risk management limits"""
    max_position_size: float = 0.1  # 10% of portfolio
    max_leverage: float = 2.0
    max_daily_loss_pct: float = 0.02  # 2% daily loss limit
    max_sector_exposure: float = 0.3
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit


class RiskManager:
    """Automated risk controls"""
    
    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()
        self.daily_loss = 0.0
        self.sector_exposure: Dict[str, float] = {}
    
    def check_position_size(self, portfolio_value: float, 
                           position_value: float) -> bool:
        """Check if position respects max position size limit"""
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 0
        return position_pct <= self.limits.max_position_size
    
    def check_leverage(self, gross_exposure: float, 
                      portfolio_value: float) -> bool:
        """Check if leverage respects limits"""
        leverage = gross_exposure / portfolio_value if portfolio_value > 0 else 0
        return leverage <= self.limits.max_leverage
    
    def check_daily_loss(self, daily_pnl: float, portfolio_value: float) -> bool:
        """Check if daily loss exceeds limit"""
        daily_loss_pct = abs(daily_pnl) / portfolio_value if portfolio_value > 0 else 0
        return daily_loss_pct <= self.limits.max_daily_loss_pct
    
    def calculate_stop_loss(self, entry_price: float) -> float:
        """Calculate stop loss price"""
        return entry_price * (1 - self.limits.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float) -> float:
        """Calculate take profit price"""
        return entry_price * (1 + self.limits.take_profit_pct)
    
    def validate_trade(self, portfolio_value: float, gross_exposure: float,
                      position_value: float, daily_pnl: float) -> tuple[bool, str]:
        """Validate trade against all risk constraints"""
        
        if not self.check_position_size(portfolio_value, position_value):
            return False, "Position size exceeds limit"
        
        if not self.check_leverage(gross_exposure, portfolio_value):
            return False, "Leverage exceeds limit"
        
        if not self.check_daily_loss(daily_pnl, portfolio_value):
            return False, "Daily loss limit breached"
        
        return True, "Trade approved"


class PositionSizer:
    """Intelligent position sizing"""
    
    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Kelly Criterion for position sizing"""
        if avg_loss == 0:
            return 0.0
        
        f_star = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        # Use fractional Kelly (25%) for safety
        return max(0, min(1, f_star * 0.25))
    
    @staticmethod
    def volatility_adjusted_size(position_size: float, 
                                volatility: float,
                                target_volatility: float = 0.15) -> float:
        """Adjust position size based on volatility"""
        if volatility <= 0:
            return position_size
        return position_size * (target_volatility / volatility)
