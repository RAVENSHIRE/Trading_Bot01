"""
The Analyst Agent - Alpha Generation with ML Stack
Runs ML models (RF, K-Means) and outputs confidence-weighted signals
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from .base_agent import BaseAgent, AgentDecision
from ..ml import RegimeDetector, AssetClusterer


class AnalystAgent(BaseAgent):
    """
    Agent 2: The Analyst - Alpha Generation
    
    Responsibilities:
    - Run K-Means clustering on assets
    - Generate trading signals using ML models
    - Calculate model confidence scores
    - Identify behavioral patterns
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="Analyst", config=config)
        
        # ML models
        self.regime_detector: Optional[RegimeDetector] = None
        self.clusterer = AssetClusterer(n_clusters=config.get("n_clusters", 5))
        
        # State
        self.current_clusters: Dict[str, int] = {}
        self.cluster_characteristics: Dict[int, Dict[str, float]] = {}
        self.model_confidence: Dict[str, float] = {}
        
        self.logger.info("Analyst Agent initialized - Alpha Generation Online")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate required inputs
        
        Required keys:
        - returns_df: DataFrame with asset returns
        - symbols: List of symbols to analyze
        """
        required_keys = ["returns_df", "symbols"]
        
        for key in required_keys:
            if key not in input_data:
                self.logger.error(f"Missing required input: {key}")
                return False
        
        returns_df = input_data["returns_df"]
        if not isinstance(returns_df, pd.DataFrame):
            self.logger.error("returns_df must be a pandas DataFrame")
            return False
        
        return True
    
    def process(self, input_data: Dict[str, Any]) -> AgentDecision:
        """
        Analyze assets and generate trading signals
        
        Args:
            input_data: Dictionary with returns data and symbols
            
        Returns:
            AgentDecision with signals and cluster assignments
        """
        returns_df = input_data["returns_df"]
        symbols = input_data["symbols"]
        market_returns = input_data.get("market_returns")
        current_regime = input_data.get("current_regime", "unknown")
        
        # Step 1: Cluster assets
        self.logger.info("Clustering assets...")
        self.clusterer.fit(returns_df, market_returns)
        self.current_clusters = self.clusterer.get_cluster_assignments(symbols)
        
        # Get cluster characteristics
        features_df = self.clusterer.extract_features(returns_df, market_returns)
        self.cluster_characteristics = self.clusterer.get_cluster_characteristics(
            features_df
        )
        cluster_names = self.clusterer.get_cluster_names(self.cluster_characteristics)
        
        # Step 2: Generate signals based on clusters and regime
        signals = self._generate_signals(
            symbols=symbols,
            cluster_assignments=self.current_clusters,
            cluster_chars=self.cluster_characteristics,
            current_regime=current_regime
        )
        
        # Step 3: Calculate model confidence
        self.model_confidence = {
            "clustering": 0.85,  # K-Means is deterministic, high confidence
            "signal_generation": 0.75,  # Heuristic-based, moderate confidence
        }
        
        # Overall confidence (average)
        overall_confidence = np.mean(list(self.model_confidence.values()))
        
        # Create reasoning
        reasoning = self._create_reasoning(
            signals=signals,
            cluster_names=cluster_names,
            current_regime=current_regime
        )
        
        # Create decision
        decision = AgentDecision(
            agent_name=self.name,
            decision_type="ALPHA_GENERATION",
            recommendation={
                "signals": signals,
                "cluster_assignments": self.current_clusters,
                "cluster_characteristics": self.cluster_characteristics,
                "cluster_names": cluster_names,
                "model_confidence": self.model_confidence
            },
            confidence=overall_confidence,
            reasoning=reasoning,
            metadata={
                "n_symbols": len(symbols),
                "n_clusters": self.clusterer.n_clusters,
                "current_regime": current_regime
            }
        )
        
        return decision
    
    def _generate_signals(
        self,
        symbols: List[str],
        cluster_assignments: Dict[str, int],
        cluster_chars: Dict[int, Dict[str, float]],
        current_regime: str
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on cluster membership and regime
        
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        for symbol in symbols:
            cluster_id = cluster_assignments.get(symbol)
            if cluster_id is None:
                continue
            
            cluster_char = cluster_chars.get(cluster_id, {})
            
            # Signal logic based on cluster characteristics and regime
            signal = self._determine_signal(
                symbol=symbol,
                cluster_char=cluster_char,
                current_regime=current_regime
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def _determine_signal(
        self,
        symbol: str,
        cluster_char: Dict[str, float],
        current_regime: str
    ) -> Optional[Dict[str, Any]]:
        """
        Determine signal for a single symbol
        
        Returns:
            Signal dictionary or None
        """
        sharpe = cluster_char.get('sharpe', 0)
        volatility = cluster_char.get('volatility', 0)
        beta = cluster_char.get('beta', 1)
        mean_return = cluster_char.get('mean_return', 0)
        
        # Default: no signal
        signal_type = "HOLD"
        strength = 0.0
        reason = "No clear signal"
        
        # BULL regime: favor high Sharpe, moderate beta
        if current_regime.lower() == "bull":
            if sharpe > 1.0 and beta < 1.5:
                signal_type = "BUY"
                strength = min(sharpe / 2.0, 1.0)
                reason = f"High Sharpe ({sharpe:.2f}) in BULL regime"
            elif beta > 2.0:
                signal_type = "HOLD"
                reason = "High beta, risky in late bull"
        
        # BEAR regime: favor low beta, defensive
        elif current_regime.lower() == "bear":
            if beta < 0.7:
                signal_type = "BUY"
                strength = 0.6
                reason = f"Defensive (beta={beta:.2f}) in BEAR regime"
            elif beta > 1.3:
                signal_type = "SELL"
                strength = 0.7
                reason = f"High beta ({beta:.2f}) in BEAR regime"
        
        # CRISIS regime: sell high volatility, hold cash
        elif current_regime.lower() == "crisis":
            if volatility > 0.03:
                signal_type = "SELL"
                strength = 0.9
                reason = f"High volatility ({volatility:.2%}) in CRISIS"
            else:
                signal_type = "HOLD"
                reason = "Low volatility, safe to hold"
        
        # RECOVERY regime: buy beaten-down high-quality
        elif current_regime.lower() == "recovery":
            if sharpe > 0.8 and mean_return < 0:
                signal_type = "BUY"
                strength = 0.8
                reason = "Quality asset at discount in RECOVERY"
        
        # SIDEWAYS regime: range-bound, favor mean reversion
        elif current_regime.lower() == "sideways":
            if abs(mean_return) < 0.001:
                signal_type = "HOLD"
                reason = "Neutral in SIDEWAYS regime"
        
        # Only return signals with strength > 0
        if strength > 0:
            return {
                "symbol": symbol,
                "signal_type": signal_type,
                "strength": strength,
                "reason": reason,
                "cluster_sharpe": sharpe,
                "cluster_beta": beta,
                "cluster_volatility": volatility
            }
        
        return None
    
    def _create_reasoning(
        self,
        signals: List[Dict[str, Any]],
        cluster_names: Dict[int, str],
        current_regime: str
    ) -> str:
        """Create human-readable reasoning"""
        
        buy_signals = [s for s in signals if s["signal_type"] == "BUY"]
        sell_signals = [s for s in signals if s["signal_type"] == "SELL"]
        
        reasoning_parts = [
            f"Regime: {current_regime.upper()}",
            f"Identified {len(signals)} actionable signals",
            f"BUY: {len(buy_signals)}, SELL: {len(sell_signals)}",
            f"Clusters: {', '.join(cluster_names.values())}"
        ]
        
        if buy_signals:
            top_buy = max(buy_signals, key=lambda x: x["strength"])
            reasoning_parts.append(
                f"Top BUY: {top_buy['symbol']} (strength={top_buy['strength']:.2f})"
            )
        
        return " | ".join(reasoning_parts)
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """
        Get summary of current clustering
        
        Returns:
            Dictionary with cluster information
        """
        return {
            "cluster_assignments": self.current_clusters,
            "cluster_characteristics": self.cluster_characteristics,
            "n_clusters": self.clusterer.n_clusters
        }
