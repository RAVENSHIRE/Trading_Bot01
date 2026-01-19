"""Position sizing implementations"""

from typing import Optional


class PositionSizer:
    """Intelligent position sizing strategies"""
    
    @staticmethod
    def fixed_fractional(portfolio_value: float, fraction: float = 0.1) -> float:
        """Fixed fractional position sizing"""
        return portfolio_value * fraction
    
    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float,
                       kelly_fraction: float = 0.25) -> float:
        """Kelly Criterion with fractional adjustment"""
        if avg_loss == 0:
            return 0.0
        
        f_star = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        return max(0, min(1, f_star * kelly_fraction))
    
    @staticmethod
    def volatility_adjusted(position_size: float, 
                           current_volatility: float,
                           target_volatility: float = 0.15) -> float:
        """Adjust position size based on volatility"""
        if current_volatility <= 0:
            return position_size
        return position_size * (target_volatility / current_volatility)
    
    @staticmethod
    def risk_based_sizing(portfolio_value: float,
                          risk_per_trade: float = 0.01,
                          stop_loss_pct: float = 0.05) -> float:
        """Size position based on risk tolerance"""
        risk_amount = portfolio_value * risk_per_trade
        shares = risk_amount / stop_loss_pct
        return shares
