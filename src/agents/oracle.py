"""
The Oracle Agent - Market Intelligence & Regime Detection
Watches news, VIX, yield curves and signals market regime shifts
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np

from .base_agent import BaseAgent, AgentDecision


class MarketRegime(Enum):
    """Market regime classifications"""
    BULL = "bull"              # Strong uptrend, low volatility
    BEAR = "bear"              # Downtrend, elevated volatility
    SIDEWAYS = "sideways"      # Range-bound, moderate volatility
    CRISIS = "crisis"          # Extreme volatility, risk-off
    RECOVERY = "recovery"      # Post-crisis stabilization


class OracleAgent(BaseAgent):
    """
    Agent 1: The Oracle - Market Intelligence
    
    Responsibilities:
    - Monitor VIX (Volatility Index)
    - Track Treasury Yield Curve
    - Analyze news sentiment
    - Detect regime changes
    - Signal market phase transitions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="Oracle", config=config)
        
        # Thresholds for regime detection
        self.vix_crisis_threshold = config.get("vix_crisis", 30.0)
        self.vix_bull_threshold = config.get("vix_bull", 15.0)
        self.yield_inversion_threshold = config.get("yield_inversion", 0.0)
        
        # State tracking
        self.current_regime: Optional[MarketRegime] = None
        self.regime_confidence = 0.0
        self.regime_duration_days = 0
        self.last_regime_change: Optional[datetime] = None
        
        self.logger.info("Oracle Agent initialized - Market Intelligence Online")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate required market data inputs
        
        Required keys:
        - vix: Current VIX value
        - spy_price: S&P 500 price
        - treasury_10y: 10-year Treasury yield
        - treasury_2y: 2-year Treasury yield
        """
        required_keys = ["vix", "spy_price", "treasury_10y", "treasury_2y"]
        
        for key in required_keys:
            if key not in input_data:
                self.logger.error(f"Missing required input: {key}")
                return False
            
            if not isinstance(input_data[key], (int, float)):
                self.logger.error(f"Invalid type for {key}: expected number")
                return False
        
        return True
    
    def process(self, input_data: Dict[str, Any]) -> AgentDecision:
        """
        Analyze market conditions and determine regime
        
        Args:
            input_data: Dictionary with market indicators
            
        Returns:
            AgentDecision with regime classification
        """
        vix = input_data["vix"]
        spy_price = input_data["spy_price"]
        treasury_10y = input_data["treasury_10y"]
        treasury_2y = input_data["treasury_2y"]
        
        # Optional inputs
        spy_ma_50 = input_data.get("spy_ma_50")
        spy_ma_200 = input_data.get("spy_ma_200")
        news_sentiment = input_data.get("news_sentiment", 0.0)  # -1 to 1
        
        # Calculate yield curve
        yield_curve = treasury_10y - treasury_2y
        
        # Regime detection logic
        regime, confidence, reasoning = self._detect_regime(
            vix=vix,
            spy_price=spy_price,
            spy_ma_50=spy_ma_50,
            spy_ma_200=spy_ma_200,
            yield_curve=yield_curve,
            news_sentiment=news_sentiment
        )
        
        # Check for regime change
        regime_changed = False
        if self.current_regime != regime:
            regime_changed = True
            self.last_regime_change = datetime.now()
            self.regime_duration_days = 0
            self.logger.warning(
                f"⚠️  REGIME CHANGE DETECTED: {self.current_regime} → {regime}"
            )
        else:
            self.regime_duration_days += 1
        
        self.current_regime = regime
        self.regime_confidence = confidence
        
        # Create decision
        decision = AgentDecision(
            agent_name=self.name,
            decision_type="REGIME_DETECTION",
            recommendation={
                "regime": regime.value,
                "regime_changed": regime_changed,
                "regime_duration_days": self.regime_duration_days
            },
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "vix": vix,
                "yield_curve": yield_curve,
                "spy_price": spy_price,
                "news_sentiment": news_sentiment,
                "last_regime_change": self.last_regime_change.isoformat() 
                    if self.last_regime_change else None
            }
        )
        
        return decision
    
    def _detect_regime(
        self, 
        vix: float,
        spy_price: float,
        spy_ma_50: Optional[float],
        spy_ma_200: Optional[float],
        yield_curve: float,
        news_sentiment: float
    ) -> tuple[MarketRegime, float, str]:
        """
        Core regime detection algorithm
        
        Returns:
            (regime, confidence, reasoning)
        """
        reasons = []
        regime_scores = {
            MarketRegime.CRISIS: 0.0,
            MarketRegime.BEAR: 0.0,
            MarketRegime.BULL: 0.0,
            MarketRegime.SIDEWAYS: 0.0,
            MarketRegime.RECOVERY: 0.0
        }
        
        # Rule 1: VIX-based classification
        if vix > self.vix_crisis_threshold:
            regime_scores[MarketRegime.CRISIS] += 0.4
            reasons.append(f"VIX extremely elevated ({vix:.1f} > {self.vix_crisis_threshold})")
        elif vix > 20:
            regime_scores[MarketRegime.BEAR] += 0.3
            reasons.append(f"VIX elevated ({vix:.1f})")
        elif vix < self.vix_bull_threshold:
            regime_scores[MarketRegime.BULL] += 0.3
            reasons.append(f"VIX low ({vix:.1f} < {self.vix_bull_threshold})")
        else:
            regime_scores[MarketRegime.SIDEWAYS] += 0.2
            reasons.append(f"VIX moderate ({vix:.1f})")
        
        # Rule 2: Yield curve
        if yield_curve < self.yield_inversion_threshold:
            regime_scores[MarketRegime.CRISIS] += 0.3
            regime_scores[MarketRegime.BEAR] += 0.2
            reasons.append(f"Yield curve inverted ({yield_curve:.2f}%)")
        elif yield_curve > 1.0:
            regime_scores[MarketRegime.BULL] += 0.2
            reasons.append(f"Yield curve steep ({yield_curve:.2f}%)")
        
        # Rule 3: Moving average trend (if available)
        if spy_ma_50 and spy_ma_200:
            if spy_price > spy_ma_50 > spy_ma_200:
                regime_scores[MarketRegime.BULL] += 0.3
                reasons.append("Strong uptrend (price > MA50 > MA200)")
            elif spy_price < spy_ma_50 < spy_ma_200:
                regime_scores[MarketRegime.BEAR] += 0.3
                reasons.append("Strong downtrend (price < MA50 < MA200)")
            elif spy_ma_50 > spy_ma_200 and spy_price < spy_ma_50:
                regime_scores[MarketRegime.SIDEWAYS] += 0.2
                reasons.append("Consolidation phase")
        
        # Rule 4: News sentiment
        if news_sentiment < -0.5:
            regime_scores[MarketRegime.CRISIS] += 0.2
            regime_scores[MarketRegime.BEAR] += 0.1
            reasons.append(f"Negative news sentiment ({news_sentiment:.2f})")
        elif news_sentiment > 0.5:
            regime_scores[MarketRegime.BULL] += 0.2
            reasons.append(f"Positive news sentiment ({news_sentiment:.2f})")
        
        # Rule 5: Recovery detection (post-crisis)
        if self.current_regime == MarketRegime.CRISIS and vix < 25:
            regime_scores[MarketRegime.RECOVERY] += 0.4
            reasons.append("Volatility declining from crisis levels")
        
        # Determine regime with highest score
        regime = max(regime_scores, key=regime_scores.get)
        confidence = regime_scores[regime]
        
        # Normalize confidence to 0-1 range
        confidence = min(confidence, 1.0)
        
        reasoning = f"Regime: {regime.value.upper()} | " + " | ".join(reasons)
        
        return regime, confidence, reasoning
    
    def get_regime_summary(self) -> Dict[str, Any]:
        """
        Get current regime summary
        
        Returns:
            Dictionary with regime information
        """
        return {
            "current_regime": self.current_regime.value if self.current_regime else None,
            "confidence": self.regime_confidence,
            "duration_days": self.regime_duration_days,
            "last_change": self.last_regime_change.isoformat() 
                if self.last_regime_change else None
        }
