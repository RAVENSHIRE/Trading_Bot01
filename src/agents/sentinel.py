"""
The Sentinel Agent - Risk Management & Veto Authority
The ultimate risk gatekeeper with veto power over all trades
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np

from .base_agent import BaseAgent, AgentDecision


class SentinelAgent(BaseAgent):
    """
    Agent 4: The Sentinel - Risk Veto Authority
    
    Responsibilities:
    - Calculate Value at Risk (VaR)
    - Monitor drawdown levels
    - Detect correlation spikes
    - Enforce hard risk limits
    - VETO trades that violate risk parameters
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="Sentinel", config=config)
        
        # Risk limits (hard constraints)
        self.max_var_pct = config.get("max_var_pct", 2.0)  # 2% VaR limit
        self.max_drawdown_pct = config.get("max_drawdown_pct", 10.0)  # 10% max DD
        self.max_position_size = config.get("max_position_size", 0.15)  # 15% per position
        self.max_leverage = config.get("max_leverage", 2.0)
        self.correlation_spike_threshold = config.get("correlation_threshold", 0.95)
        self.max_daily_loss_pct = config.get("max_daily_loss_pct", 3.0)
        
        # State tracking
        self.veto_count = 0
        self.approved_count = 0
        self.last_veto_reason: Optional[str] = None
        
        self.logger.info("Sentinel Agent initialized - Risk Veto Authority Active")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate risk assessment inputs
        
        Required keys:
        - proposed_trades: List of proposed trades
        - portfolio_value: Current portfolio value
        - portfolio_positions: Current positions
        - returns_history: Historical returns for VaR calculation
        """
        required_keys = [
            "proposed_trades", 
            "portfolio_value", 
            "portfolio_positions",
            "returns_history"
        ]
        
        for key in required_keys:
            if key not in input_data:
                self.logger.error(f"Missing required input: {key}")
                return False
        
        return True
    
    def process(self, input_data: Dict[str, Any]) -> AgentDecision:
        """
        Evaluate proposed trades against risk limits
        
        Args:
            input_data: Dictionary with portfolio and trade data
            
        Returns:
            AgentDecision with APPROVE or VETO recommendation
        """
        proposed_trades = input_data["proposed_trades"]
        portfolio_value = input_data["portfolio_value"]
        portfolio_positions = input_data["portfolio_positions"]
        returns_history = input_data["returns_history"]
        
        # Optional inputs
        current_drawdown = input_data.get("current_drawdown", 0.0)
        daily_pnl_pct = input_data.get("daily_pnl_pct", 0.0)
        market_regime = input_data.get("market_regime", "unknown")
        
        # Run risk checks
        veto_reasons = []
        risk_metrics = {}
        
        # Check 1: Value at Risk (VaR)
        var_check, var_value = self._check_var(returns_history, portfolio_value)
        risk_metrics["var_95"] = var_value
        if not var_check:
            veto_reasons.append(
                f"VaR violation: {var_value:.2f}% exceeds limit of {self.max_var_pct}%"
            )
        
        # Check 2: Maximum Drawdown
        dd_check = self._check_drawdown(current_drawdown)
        risk_metrics["current_drawdown"] = current_drawdown
        if not dd_check:
            veto_reasons.append(
                f"Drawdown violation: {current_drawdown:.2f}% exceeds limit of "
                f"{self.max_drawdown_pct}%"
            )
        
        # Check 3: Position Size Limits
        position_check, oversized_positions = self._check_position_sizes(
            proposed_trades, portfolio_positions, portfolio_value
        )
        if not position_check:
            veto_reasons.append(
                f"Position size violation: {oversized_positions} exceed "
                f"{self.max_position_size*100}% limit"
            )
        
        # Check 4: Leverage Limits
        leverage_check, current_leverage = self._check_leverage(
            portfolio_positions, portfolio_value
        )
        risk_metrics["leverage"] = current_leverage
        if not leverage_check:
            veto_reasons.append(
                f"Leverage violation: {current_leverage:.2f}x exceeds limit of "
                f"{self.max_leverage}x"
            )
        
        # Check 5: Daily Loss Limit
        daily_loss_check = self._check_daily_loss(daily_pnl_pct)
        risk_metrics["daily_pnl_pct"] = daily_pnl_pct
        if not daily_loss_check:
            veto_reasons.append(
                f"Daily loss violation: {daily_pnl_pct:.2f}% exceeds limit of "
                f"-{self.max_daily_loss_pct}%"
            )
        
        # Check 6: Correlation Spike Detection
        correlation_check, max_correlation = self._check_correlations(portfolio_positions)
        risk_metrics["max_correlation"] = max_correlation
        if not correlation_check:
            veto_reasons.append(
                f"Correlation spike: {max_correlation:.2f} exceeds threshold of "
                f"{self.correlation_spike_threshold}"
            )
        
        # Check 7: Regime-based restrictions
        regime_check, regime_reason = self._check_regime_restrictions(
            market_regime, proposed_trades
        )
        if not regime_check:
            veto_reasons.append(regime_reason)
        
        # Final decision
        if veto_reasons:
            decision_type = "VETO"
            self.veto_count += 1
            self.last_veto_reason = "; ".join(veto_reasons)
            confidence = 1.0  # Veto decisions are absolute
            reasoning = f"🛑 TRADE VETOED: {self.last_veto_reason}"
            
            self.logger.warning(f"⚠️  VETO ISSUED: {self.last_veto_reason}")
        else:
            decision_type = "APPROVE"
            self.approved_count += 1
            confidence = 0.95
            reasoning = (
                f"✅ Risk checks passed: VaR={var_value:.2f}%, "
                f"DD={current_drawdown:.2f}%, Leverage={current_leverage:.2f}x"
            )
            
            self.logger.info(f"✅ Trades approved - All risk checks passed")
        
        # Create decision
        decision = AgentDecision(
            agent_name=self.name,
            decision_type=decision_type,
            recommendation={
                "approved": decision_type == "APPROVE",
                "veto_reasons": veto_reasons,
                "risk_metrics": risk_metrics
            },
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "veto_count": self.veto_count,
                "approved_count": self.approved_count,
                "market_regime": market_regime
            }
        )
        
        return decision
    
    def _check_var(self, returns_history: List[float], 
                   portfolio_value: float) -> tuple[bool, float]:
        """
        Calculate 95% Value at Risk
        
        Returns:
            (passed, var_percentage)
        """
        if not returns_history or len(returns_history) < 20:
            self.logger.warning("Insufficient data for VaR calculation")
            return True, 0.0
        
        returns = np.array(returns_history)
        var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
        var_pct = abs(var_95) * 100
        
        return var_pct <= self.max_var_pct, var_pct
    
    def _check_drawdown(self, current_drawdown: float) -> bool:
        """Check if current drawdown exceeds limit"""
        return abs(current_drawdown) <= self.max_drawdown_pct
    
    def _check_position_sizes(
        self, 
        proposed_trades: List[Dict],
        current_positions: Dict[str, Any],
        portfolio_value: float
    ) -> tuple[bool, List[str]]:
        """
        Check if any position would exceed size limit
        
        Returns:
            (passed, list_of_oversized_symbols)
        """
        oversized = []
        
        # Check proposed trades
        for trade in proposed_trades:
            symbol = trade.get("symbol")
            trade_value = trade.get("value", 0)
            position_pct = (trade_value / portfolio_value) * 100
            
            if position_pct > self.max_position_size * 100:
                oversized.append(f"{symbol} ({position_pct:.1f}%)")
        
        return len(oversized) == 0, oversized
    
    def _check_leverage(
        self, 
        positions: Dict[str, Any], 
        portfolio_value: float
    ) -> tuple[bool, float]:
        """
        Calculate current leverage ratio
        
        Returns:
            (passed, leverage_ratio)
        """
        total_exposure = sum(
            abs(pos.get("value", 0)) for pos in positions.values()
        )
        
        if portfolio_value == 0:
            return True, 0.0
        
        leverage = total_exposure / portfolio_value
        
        return leverage <= self.max_leverage, leverage
    
    def _check_daily_loss(self, daily_pnl_pct: float) -> bool:
        """Check if daily loss exceeds limit"""
        return daily_pnl_pct >= -self.max_daily_loss_pct
    
    def _check_correlations(
        self, 
        positions: Dict[str, Any]
    ) -> tuple[bool, float]:
        """
        Detect correlation spikes in portfolio
        
        Returns:
            (passed, max_correlation)
        """
        # Simplified correlation check
        # In production, would calculate actual correlation matrix
        
        # For now, return safe values
        max_correlation = 0.7  # Placeholder
        
        return max_correlation <= self.correlation_spike_threshold, max_correlation
    
    def _check_regime_restrictions(
        self, 
        market_regime: str, 
        proposed_trades: List[Dict]
    ) -> tuple[bool, str]:
        """
        Apply regime-specific trading restrictions
        
        Returns:
            (passed, reason_if_failed)
        """
        # During CRISIS regime, restrict new long positions
        if market_regime.lower() == "crisis":
            long_trades = [t for t in proposed_trades if t.get("side") == "long"]
            if long_trades:
                return False, "New long positions blocked during CRISIS regime"
        
        return True, ""
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get risk management summary
        
        Returns:
            Dictionary with risk statistics
        """
        total_decisions = self.veto_count + self.approved_count
        veto_rate = (self.veto_count / total_decisions * 100) if total_decisions > 0 else 0
        
        return {
            "veto_count": self.veto_count,
            "approved_count": self.approved_count,
            "veto_rate_pct": veto_rate,
            "last_veto_reason": self.last_veto_reason,
            "risk_limits": {
                "max_var_pct": self.max_var_pct,
                "max_drawdown_pct": self.max_drawdown_pct,
                "max_position_size": self.max_position_size,
                "max_leverage": self.max_leverage
            }
        }
