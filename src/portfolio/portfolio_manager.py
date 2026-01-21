"""
Portfolio and Risk Layer - Portfolio management and risk monitoring
Part of the 5-Layer Hedge Fund Architecture
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a portfolio position"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    entry_date: str
    
    @property
    def value(self) -> float:
        """Current position value"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis"""
        return self.quantity * self.entry_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L"""
        return self.value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L percentage"""
        if self.cost_basis == 0:
            return 0
        return self.unrealized_pnl / self.cost_basis


@dataclass
class RiskMetrics:
    """Portfolio risk metrics"""
    var_95: float  # Value at Risk at 95% confidence
    max_drawdown: float
    current_leverage: float
    portfolio_volatility: float
    concentration_risk: float  # Largest position as % of portfolio
    
    def is_within_limits(
        self,
        var_limit: float = 0.02,
        dd_limit: float = 0.20,
        leverage_limit: float = 2.0
    ) -> bool:
        """Check if metrics are within limits"""
        return (
            self.var_95 <= var_limit and
            abs(self.max_drawdown) <= dd_limit and
            self.current_leverage <= leverage_limit
        )


class PortfolioOptimizer:
    """Optimizes portfolio weights"""
    
    @staticmethod
    def mean_variance_optimization(
        returns: pd.DataFrame,
        target_return: float = 0.10,
        max_weight: float = 0.20,
        min_weight: float = 0.01
    ) -> Dict[str, float]:
        """
        Mean-Variance optimization (Markowitz)
        
        Args:
            returns: DataFrame of returns
            target_return: Target annual return
            max_weight: Maximum weight per position
            min_weight: Minimum weight per position
            
        Returns:
            Dictionary of optimal weights
        """
        try:
            from scipy.optimize import minimize
        except ImportError:
            logger.error("scipy not available for optimization")
            return {}
        
        n_assets = len(returns.columns)
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_vol = portfolio_volatility(weights)
            return -portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]
        
        # Bounds
        bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
        
        # Initial guess
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            negative_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            weights = result.x
        else:
            weights = initial_weights
        
        # Create weights dictionary
        return {
            symbol: float(weight)
            for symbol, weight in zip(returns.columns, weights)
            if weight >= min_weight
        }
    
    @staticmethod
    def risk_parity_allocation(
        returns: pd.DataFrame,
        max_weight: float = 0.20,
        min_weight: float = 0.01
    ) -> Dict[str, float]:
        """
        Risk-Parity allocation
        
        Allocates weights so each asset contributes equally to portfolio risk
        """
        # Calculate volatilities
        volatilities = returns.std() * np.sqrt(252)
        
        # Inverse volatility weights
        inv_vol = 1.0 / volatilities
        weights = inv_vol / inv_vol.sum()
        
        # Apply constraints
        weights = np.clip(weights, min_weight, max_weight)
        weights = weights / weights.sum()
        
        return {
            symbol: float(weight)
            for symbol, weight in zip(returns.columns, weights)
        }
    
    @staticmethod
    def equal_weight_allocation(symbols: List[str]) -> Dict[str, float]:
        """Simple equal-weight allocation"""
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}


class RiskMonitor:
    """Monitors portfolio risk"""
    
    @staticmethod
    def calculate_var(
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk
        
        Args:
            returns: Series of returns
            confidence_level: Confidence level (0.95 = 95%)
            
        Returns:
            VaR (negative value)
        """
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown"""
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown.min()
    
    @staticmethod
    def calculate_portfolio_volatility(
        positions: Dict[str, float],
        returns: pd.DataFrame
    ) -> float:
        """
        Calculate portfolio volatility
        
        Args:
            positions: Dictionary of position weights
            returns: DataFrame of returns
            
        Returns:
            Portfolio volatility (annualized)
        """
        # Get returns for positions
        position_returns = returns[[s for s in positions.keys() if s in returns.columns]]
        
        if len(position_returns.columns) == 0:
            return 0
        
        # Align weights
        weights = np.array([positions.get(s, 0) for s in position_returns.columns])
        
        # Calculate covariance
        cov_matrix = position_returns.cov() * 252
        
        # Calculate volatility
        portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
        return np.sqrt(portfolio_var)
    
    @staticmethod
    def calculate_concentration_risk(positions: Dict[str, float]) -> float:
        """
        Calculate concentration risk (largest position as % of portfolio)
        
        Args:
            positions: Dictionary of position values
            
        Returns:
            Concentration risk (0-1)
        """
        if not positions:
            return 0
        
        total_value = sum(abs(v) for v in positions.values())
        if total_value == 0:
            return 0
        
        largest_position = max(abs(v) for v in positions.values())
        return largest_position / total_value
    
    @staticmethod
    def calculate_risk_metrics(
        positions: Dict[str, Position],
        returns: pd.DataFrame,
        equity_curve: pd.Series,
        portfolio_value: float
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics
        
        Args:
            positions: Dictionary of positions
            returns: DataFrame of returns
            equity_curve: Series of portfolio values
            portfolio_value: Current portfolio value
            
        Returns:
            RiskMetrics object
        """
        # VaR
        daily_returns = equity_curve.pct_change().dropna()
        var_95 = RiskMonitor.calculate_var(daily_returns, 0.95)
        
        # Max Drawdown
        max_dd = RiskMonitor.calculate_max_drawdown(equity_curve)
        
        # Leverage
        total_long = sum(p.value for p in positions.values() if p.quantity > 0)
        total_short = sum(abs(p.value) for p in positions.values() if p.quantity < 0)
        current_leverage = (total_long + total_short) / portfolio_value if portfolio_value > 0 else 0
        
        # Volatility
        position_weights = {p.symbol: p.value / portfolio_value for p in positions.values()}
        portfolio_vol = RiskMonitor.calculate_portfolio_volatility(position_weights, returns)
        
        # Concentration
        concentration = RiskMonitor.calculate_concentration_risk(
            {p.symbol: p.value for p in positions.values()}
        )
        
        return RiskMetrics(
            var_95=abs(var_95),
            max_drawdown=max_dd,
            current_leverage=current_leverage,
            portfolio_volatility=portfolio_vol,
            concentration_risk=concentration
        )


class PositionSizer:
    """Calculates position sizes"""
    
    @staticmethod
    def kelly_criterion(
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion position size
        
        Args:
            win_rate: Probability of winning trade
            avg_win: Average win size
            avg_loss: Average loss size
            
        Returns:
            Fraction of portfolio to risk
        """
        if avg_loss == 0:
            return 0
        
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        
        # Use half-Kelly for safety
        return max(0, min(kelly / 2, 0.25))
    
    @staticmethod
    def volatility_based_sizing(
        portfolio_value: float,
        target_volatility: float,
        asset_volatility: float,
        max_position_size: float = 0.20
    ) -> float:
        """
        Calculate position size based on volatility
        
        Args:
            portfolio_value: Total portfolio value
            target_volatility: Target portfolio volatility
            asset_volatility: Asset volatility
            max_position_size: Maximum position as % of portfolio
            
        Returns:
            Position size in dollars
        """
        if asset_volatility == 0:
            return 0
        
        # Calculate position size to achieve target volatility
        position_pct = target_volatility / asset_volatility
        position_pct = min(position_pct, max_position_size)
        
        return portfolio_value * position_pct
    
    @staticmethod
    def fixed_fractional_sizing(
        portfolio_value: float,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.05
    ) -> float:
        """
        Calculate position size using fixed fractional method
        
        Args:
            portfolio_value: Total portfolio value
            risk_per_trade: Risk per trade as % of portfolio
            stop_loss_pct: Stop loss distance as % of entry price
            
        Returns:
            Position size in dollars
        """
        risk_amount = portfolio_value * risk_per_trade
        position_size = risk_amount / stop_loss_pct
        
        return position_size


class PortfolioManager:
    """Main portfolio management interface"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.optimizer = PortfolioOptimizer()
        self.risk_monitor = RiskMonitor()
        self.position_sizer = PositionSizer()
    
    def add_position(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        current_price: float
    ) -> None:
        """Add or update a position"""
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            entry_date=str(datetime.utcnow().date())
        )
    
    def remove_position(self, symbol: str) -> None:
        """Remove a position"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        return sum(p.value for p in self.positions.values())
    
    def get_portfolio_weights(self) -> Dict[str, float]:
        """Get portfolio weights"""
        total_value = self.get_portfolio_value()
        if total_value == 0:
            return {}
        
        return {
            p.symbol: p.value / total_value
            for p in self.positions.values()
        }
    
    def get_risk_metrics(
        self,
        returns: pd.DataFrame,
        equity_curve: pd.Series
    ) -> RiskMetrics:
        """Calculate risk metrics"""
        portfolio_value = self.get_portfolio_value()
        return self.risk_monitor.calculate_risk_metrics(
            self.positions,
            returns,
            equity_curve,
            portfolio_value
        )
    
    def optimize_weights(
        self,
        returns: pd.DataFrame,
        method: str = "mean_variance"
    ) -> Dict[str, float]:
        """Optimize portfolio weights"""
        if method == "mean_variance":
            return self.optimizer.mean_variance_optimization(returns)
        elif method == "risk_parity":
            return self.optimizer.risk_parity_allocation(returns)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
