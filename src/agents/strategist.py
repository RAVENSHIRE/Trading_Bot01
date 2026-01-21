"""
The Strategist Agent - Portfolio Optimization
Optimizes portfolio weights using Mean-Variance and Risk-Parity logic
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .base_agent import BaseAgent, AgentDecision


class StrategistAgent(BaseAgent):
    """
    Agent 3: The Strategist - Portfolio Optimizer
    
    Responsibilities:
    - Optimize portfolio weights
    - Calculate expected return and volatility
    - Apply Mean-Variance optimization (Markowitz)
    - Implement Risk-Parity allocation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="Strategist", config=config)
        
        # Configuration
        self.optimization_method = config.get("method", "mean_variance")  # or "risk_parity"
        self.target_return = config.get("target_return", 0.10)  # 10% annual
        self.max_weight = config.get("max_weight", 0.20)  # 20% per position
        self.min_weight = config.get("min_weight", 0.01)  # 1% minimum
        
        # State
        self.optimal_weights: Dict[str, float] = {}
        self.expected_return = 0.0
        self.expected_volatility = 0.0
        self.sharpe_ratio = 0.0
        
        self.logger.info(
            f"Strategist Agent initialized - Method: {self.optimization_method}"
        )
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate required inputs
        
        Required keys:
        - signals: List of trading signals from Analyst
        - returns_df: DataFrame with historical returns
        - current_portfolio: Current portfolio positions
        """
        required_keys = ["signals", "returns_df", "current_portfolio"]
        
        for key in required_keys:
            if key not in input_data:
                self.logger.error(f"Missing required input: {key}")
                return False
        
        return True
    
    def process(self, input_data: Dict[str, Any]) -> AgentDecision:
        """
        Optimize portfolio based on signals
        
        Args:
            input_data: Dictionary with signals and returns data
            
        Returns:
            AgentDecision with optimal weights
        """
        signals = input_data["signals"]
        returns_df = input_data["returns_df"]
        current_portfolio = input_data["current_portfolio"]
        portfolio_value = input_data.get("portfolio_value", 100000)
        
        # Filter signals to get tradeable symbols
        buy_signals = [s for s in signals if s["signal_type"] == "BUY"]
        
        if not buy_signals:
            self.logger.info("No BUY signals, maintaining current portfolio")
            return self._create_hold_decision(current_portfolio)
        
        # Extract symbols and signal strengths
        symbols = [s["symbol"] for s in buy_signals]
        signal_strengths = {s["symbol"]: s["strength"] for s in buy_signals}
        
        # Get returns for these symbols
        returns_subset = returns_df[symbols].dropna()
        
        if len(returns_subset) < 20:
            self.logger.warning("Insufficient data for optimization")
            return self._create_hold_decision(current_portfolio)
        
        # Optimize portfolio
        if self.optimization_method == "mean_variance":
            weights = self._optimize_mean_variance(returns_subset, signal_strengths)
        elif self.optimization_method == "risk_parity":
            weights = self._optimize_risk_parity(returns_subset)
        else:
            weights = self._optimize_equal_weight(symbols)
        
        # Calculate expected metrics
        self.optimal_weights = weights
        self.expected_return, self.expected_volatility = self._calculate_portfolio_metrics(
            returns_subset, weights
        )
        self.sharpe_ratio = (
            self.expected_return / self.expected_volatility 
            if self.expected_volatility > 0 else 0
        )
        
        # Create trades to rebalance
        trades = self._create_rebalancing_trades(
            optimal_weights=weights,
            current_portfolio=current_portfolio,
            portfolio_value=portfolio_value
        )
        
        # Create reasoning
        reasoning = self._create_reasoning(weights, trades)
        
        # Create decision
        decision = AgentDecision(
            agent_name=self.name,
            decision_type="PORTFOLIO_OPTIMIZATION",
            recommendation={
                "optimal_weights": weights,
                "trades": trades,
                "expected_return": self.expected_return,
                "expected_volatility": self.expected_volatility,
                "sharpe_ratio": self.sharpe_ratio
            },
            confidence=0.80,
            reasoning=reasoning,
            metadata={
                "n_positions": len(weights),
                "optimization_method": self.optimization_method
            }
        )
        
        return decision
    
    def _optimize_mean_variance(
        self, 
        returns_df: pd.DataFrame,
        signal_strengths: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Mean-Variance optimization (Markowitz)
        
        Maximizes Sharpe ratio subject to constraints
        """
        symbols = returns_df.columns.tolist()
        n_assets = len(symbols)
        
        # Calculate expected returns and covariance
        mean_returns = returns_df.mean()
        cov_matrix = returns_df.cov()
        
        # Adjust expected returns by signal strength
        for symbol in symbols:
            strength = signal_strengths.get(symbol, 0.5)
            mean_returns[symbol] *= (1 + strength)
        
        # Objective: Minimize negative Sharpe ratio
        def objective(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            sharpe = -portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
            return sharpe
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # Weights sum to 1
        ]
        
        # Bounds
        bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
        
        # Initial guess (equal weight)
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            optimal_weights = result.x
        else:
            self.logger.warning("Optimization failed, using equal weights")
            optimal_weights = initial_weights
        
        # Create weights dictionary
        weights = {
            symbol: float(weight)
            for symbol, weight in zip(symbols, optimal_weights)
            if weight >= self.min_weight
        }
        
        return weights
    
    def _optimize_risk_parity(self, returns_df: pd.DataFrame) -> Dict[str, float]:
        """
        Risk-Parity optimization
        
        Allocates weights such that each asset contributes equally to portfolio risk
        """
        symbols = returns_df.columns.tolist()
        n_assets = len(symbols)
        
        # Calculate covariance matrix
        cov_matrix = returns_df.cov()
        
        # Objective: Minimize sum of squared differences in risk contribution
        def objective(weights):
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            
            # Marginal risk contribution
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            
            # Risk contribution
            risk_contrib = weights * marginal_contrib
            
            # Target: equal risk contribution
            target_risk = portfolio_vol / n_assets
            
            # Sum of squared deviations
            return np.sum((risk_contrib - target_risk) ** 2)
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]
        
        # Bounds
        bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
        
        # Initial guess
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            optimal_weights = result.x
        else:
            self.logger.warning("Risk-parity optimization failed, using equal weights")
            optimal_weights = initial_weights
        
        # Create weights dictionary
        weights = {
            symbol: float(weight)
            for symbol, weight in zip(symbols, optimal_weights)
            if weight >= self.min_weight
        }
        
        return weights
    
    def _optimize_equal_weight(self, symbols: List[str]) -> Dict[str, float]:
        """Simple equal-weight allocation"""
        n = len(symbols)
        weight = 1.0 / n
        
        return {symbol: weight for symbol in symbols}
    
    def _calculate_portfolio_metrics(
        self, 
        returns_df: pd.DataFrame,
        weights: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        Calculate expected return and volatility
        
        Returns:
            (expected_return, expected_volatility)
        """
        symbols = list(weights.keys())
        weight_array = np.array([weights[s] for s in symbols])
        
        # Expected return
        mean_returns = returns_df[symbols].mean()
        expected_return = np.dot(weight_array, mean_returns)
        
        # Expected volatility
        cov_matrix = returns_df[symbols].cov()
        expected_variance = np.dot(weight_array, np.dot(cov_matrix, weight_array))
        expected_volatility = np.sqrt(expected_variance)
        
        # Annualize (assuming daily returns)
        expected_return_annual = expected_return * 252
        expected_volatility_annual = expected_volatility * np.sqrt(252)
        
        return expected_return_annual, expected_volatility_annual
    
    def _create_rebalancing_trades(
        self,
        optimal_weights: Dict[str, float],
        current_portfolio: Dict[str, Any],
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """
        Create trades to rebalance to optimal weights
        
        Returns:
            List of trade dictionaries
        """
        trades = []
        
        # Calculate current weights
        current_weights = {}
        for symbol, position in current_portfolio.items():
            position_value = position.get("value", 0)
            current_weights[symbol] = position_value / portfolio_value
        
        # Calculate weight changes
        for symbol, target_weight in optimal_weights.items():
            current_weight = current_weights.get(symbol, 0.0)
            weight_change = target_weight - current_weight
            
            if abs(weight_change) > 0.01:  # Only trade if change > 1%
                trade_value = weight_change * portfolio_value
                
                trades.append({
                    "symbol": symbol,
                    "side": "buy" if weight_change > 0 else "sell",
                    "value": abs(trade_value),
                    "target_weight": target_weight,
                    "current_weight": current_weight,
                    "weight_change": weight_change
                })
        
        # Close positions not in optimal portfolio
        for symbol in current_weights:
            if symbol not in optimal_weights and current_weights[symbol] > 0.01:
                trades.append({
                    "symbol": symbol,
                    "side": "sell",
                    "value": current_weights[symbol] * portfolio_value,
                    "target_weight": 0.0,
                    "current_weight": current_weights[symbol],
                    "weight_change": -current_weights[symbol]
                })
        
        return trades
    
    def _create_hold_decision(self, current_portfolio: Dict[str, Any]) -> AgentDecision:
        """Create a HOLD decision when no changes needed"""
        return AgentDecision(
            agent_name=self.name,
            decision_type="PORTFOLIO_HOLD",
            recommendation={
                "action": "HOLD",
                "current_portfolio": current_portfolio
            },
            confidence=0.90,
            reasoning="No actionable signals, maintaining current portfolio"
        )
    
    def _create_reasoning(
        self, 
        weights: Dict[str, float],
        trades: List[Dict[str, Any]]
    ) -> str:
        """Create human-readable reasoning"""
        
        n_positions = len(weights)
        n_trades = len(trades)
        
        top_positions = sorted(
            weights.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        reasoning_parts = [
            f"Optimized portfolio: {n_positions} positions",
            f"Expected Return: {self.expected_return:.2%}",
            f"Expected Volatility: {self.expected_volatility:.2%}",
            f"Sharpe Ratio: {self.sharpe_ratio:.2f}",
            f"Rebalancing trades: {n_trades}",
            f"Top positions: {', '.join([f'{s} ({w:.1%})' for s, w in top_positions])}"
        ]
        
        return " | ".join(reasoning_parts)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get summary of current portfolio optimization
        
        Returns:
            Dictionary with portfolio metrics
        """
        return {
            "optimal_weights": self.optimal_weights,
            "expected_return": self.expected_return,
            "expected_volatility": self.expected_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "n_positions": len(self.optimal_weights)
        }
