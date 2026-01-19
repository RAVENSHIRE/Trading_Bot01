"""Signal generation engine"""

import pandas as pd
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """Signal types"""
    BUY = 1
    SELL = -1
    NEUTRAL = 0


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    signal_type: SignalType
    strength: float  # 0-1 confidence score
    timestamp: str
    reason: str = ""


class SignalGenerator:
    """Generate trading signals from price/fundamental data"""
    
    def __init__(self):
        self.signals: Dict[str, List[Signal]] = {}
    
    def momentum_signal(self, prices: pd.Series, fast_period: int = 20, 
                       slow_period: int = 50) -> SignalType:
        """Generate momentum signal using moving averages"""
        if len(prices) < slow_period:
            return SignalType.NEUTRAL
        
        fast_ma = prices.rolling(window=fast_period).mean().iloc[-1]
        slow_ma = prices.rolling(window=slow_period).mean().iloc[-1]
        current_price = prices.iloc[-1]
        
        if fast_ma > slow_ma and current_price > fast_ma:
            return SignalType.BUY
        elif fast_ma < slow_ma and current_price < fast_ma:
            return SignalType.SELL
        return SignalType.NEUTRAL
    
    def mean_reversion_signal(self, prices: pd.Series, period: int = 20, 
                              std_dev: float = 2.0) -> SignalType:
        """Generate mean reversion signal using Bollinger Bands"""
        if len(prices) < period:
            return SignalType.NEUTRAL
        
        sma = prices.rolling(window=period).mean().iloc[-1]
        std = prices.rolling(window=period).std().iloc[-1]
        current_price = prices.iloc[-1]
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        if current_price < lower_band:
            return SignalType.BUY
        elif current_price > upper_band:
            return SignalType.SELL
        return SignalType.NEUTRAL
    
    def generate_signal(self, symbol: str, signal_type: SignalType, 
                       strength: float, timestamp: str, reason: str = "") -> Signal:
        """Generate and store signal"""
        signal = Signal(
            symbol=symbol,
            signal_type=signal_type,
            strength=max(0, min(1, strength)),
            timestamp=timestamp,
            reason=reason
        )
        
        if symbol not in self.signals:
            self.signals[symbol] = []
        self.signals[symbol].append(signal)
        
        return signal
    
    def get_latest_signal(self, symbol: str) -> Optional[Signal]:
        """Get latest signal for a symbol"""
        if symbol not in self.signals or not self.signals[symbol]:
            return None
        return self.signals[symbol][-1]
