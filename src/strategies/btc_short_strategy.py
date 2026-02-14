"""
BTC Short Trading Strategy

Generates short signals for Bitcoin using technical indicators optimized
for identifying overbought conditions and trend reversals. Designed to
work with MetaTrader 5 (CFD) and Swissquote Advanced Trade platforms.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BTCSignal(Enum):
    """BTC trading signal types"""
    STRONG_SHORT = "STRONG_SHORT"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    CLOSE_SHORT = "CLOSE_SHORT"


@dataclass
class BTCShortSignal:
    """A BTC short trading signal with metadata"""
    signal: BTCSignal
    confidence: float  # 0.0 - 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None
    reasons: List[str] = field(default_factory=list)
    indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class BTCShortConfig:
    """Configuration for BTC short strategy"""
    # RSI parameters
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_extreme_overbought: float = 80.0

    # MACD parameters
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Bollinger Bands
    bb_period: int = 20
    bb_std: float = 2.0

    # EMA for trend
    ema_short: int = 9
    ema_long: int = 21

    # Volume
    volume_spike_multiplier: float = 1.5

    # Risk management
    stop_loss_pct: float = 0.03  # 3% stop loss for BTC shorts
    take_profit_pct: float = 0.06  # 6% take profit (2:1 reward/risk)
    max_position_pct: float = 0.05  # Max 5% of portfolio in BTC short

    # Funding rate threshold (for perps/CFDs)
    funding_rate_threshold: float = 0.01  # 1% signals overheated longs


class BTCShortStrategy:
    """
    BTC Short Trading Strategy

    Combines multiple technical indicators to identify short opportunities:
    - RSI overbought conditions
    - MACD bearish crossovers
    - Bollinger Band upper rejections
    - EMA death crosses
    - Volume divergences
    """

    def __init__(self, config: Optional[BTCShortConfig] = None):
        self.config = config or BTCShortConfig()
        self.signal_history: List[BTCShortSignal] = []
        logger.info("BTCShortStrategy initialized")

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=self.config.rsi_period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.config.rsi_period, min_periods=1).mean()

        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def calculate_macd(self, prices: pd.Series) -> tuple:
        """Calculate MACD, signal line, and histogram"""
        ema_fast = prices.ewm(span=self.config.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.config.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.config.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, prices: pd.Series) -> tuple:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=self.config.bb_period).mean()
        std = prices.rolling(window=self.config.bb_period).std()
        upper = sma + (self.config.bb_std * std)
        lower = sma - (self.config.bb_std * std)
        return upper, sma, lower

    def calculate_emas(self, prices: pd.Series) -> tuple:
        """Calculate short and long EMAs"""
        ema_short = prices.ewm(span=self.config.ema_short, adjust=False).mean()
        ema_long = prices.ewm(span=self.config.ema_long, adjust=False).mean()
        return ema_short, ema_long

    def detect_volume_spike(self, volume: pd.Series) -> bool:
        """Detect if current volume is significantly above average"""
        if len(volume) < 20:
            return False
        avg_volume = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        return current_volume > avg_volume * self.config.volume_spike_multiplier

    def analyze(
        self,
        prices: pd.Series,
        volume: Optional[pd.Series] = None,
        funding_rate: Optional[float] = None,
    ) -> BTCShortSignal:
        """
        Analyze BTC price data and generate a short signal.

        Args:
            prices: OHLC close prices (at least 50 data points recommended)
            volume: Volume data (optional, improves signal quality)
            funding_rate: Current perpetual funding rate (optional)

        Returns:
            BTCShortSignal with recommendation and metadata
        """
        if len(prices) < self.config.macd_slow + self.config.macd_signal:
            return BTCShortSignal(
                signal=BTCSignal.NEUTRAL,
                confidence=0.0,
                timestamp=datetime.now(),
                reasons=["Insufficient data for analysis"],
            )

        current_price = float(prices.iloc[-1])
        reasons = []
        score = 0.0
        indicators = {}

        # 1. RSI Analysis
        rsi = self.calculate_rsi(prices)
        current_rsi = float(rsi.iloc[-1])
        indicators["rsi"] = current_rsi

        if current_rsi >= self.config.rsi_extreme_overbought:
            score += 0.3
            reasons.append(f"RSI extremely overbought at {current_rsi:.1f}")
        elif current_rsi >= self.config.rsi_overbought:
            score += 0.2
            reasons.append(f"RSI overbought at {current_rsi:.1f}")

        # 2. MACD Analysis
        macd_line, signal_line, histogram = self.calculate_macd(prices)
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        current_hist = float(histogram.iloc[-1])
        prev_hist = float(histogram.iloc[-2])
        indicators["macd"] = current_macd
        indicators["macd_signal"] = current_signal
        indicators["macd_histogram"] = current_hist

        # Bearish crossover: MACD crosses below signal
        if current_macd < current_signal and float(macd_line.iloc[-2]) >= float(
            signal_line.iloc[-2]
        ):
            score += 0.25
            reasons.append("MACD bearish crossover")
        # Declining histogram
        elif current_hist < prev_hist and current_hist < 0:
            score += 0.1
            reasons.append("MACD histogram declining in negative territory")

        # 3. Bollinger Bands
        upper, sma, lower = self.calculate_bollinger_bands(prices)
        current_upper = float(upper.iloc[-1])
        current_sma = float(sma.iloc[-1])
        indicators["bb_upper"] = current_upper
        indicators["bb_middle"] = current_sma
        indicators["bb_lower"] = float(lower.iloc[-1])

        # Price near or above upper band = overbought
        bb_position = (current_price - current_sma) / (current_upper - current_sma) if (
            current_upper - current_sma
        ) != 0 else 0
        indicators["bb_position"] = bb_position

        if current_price >= current_upper:
            score += 0.2
            reasons.append("Price at/above upper Bollinger Band")
        elif bb_position > 0.8:
            score += 0.1
            reasons.append("Price near upper Bollinger Band")

        # 4. EMA Analysis
        ema_short, ema_long = self.calculate_emas(prices)
        current_ema_short = float(ema_short.iloc[-1])
        current_ema_long = float(ema_long.iloc[-1])
        prev_ema_short = float(ema_short.iloc[-2])
        prev_ema_long = float(ema_long.iloc[-2])
        indicators["ema_short"] = current_ema_short
        indicators["ema_long"] = current_ema_long

        # Death cross: short EMA crosses below long EMA
        if current_ema_short < current_ema_long and prev_ema_short >= prev_ema_long:
            score += 0.25
            reasons.append("EMA death cross (bearish)")
        elif current_ema_short < current_ema_long:
            score += 0.1
            reasons.append("Short EMA below long EMA (bearish trend)")

        # 5. Volume Analysis
        if volume is not None and len(volume) >= 20:
            has_spike = self.detect_volume_spike(volume)
            indicators["volume_spike"] = 1.0 if has_spike else 0.0
            if has_spike and current_price < float(prices.iloc[-2]):
                score += 0.15
                reasons.append("High volume on price decline (bearish)")

        # 6. Funding Rate (for perpetuals/CFDs)
        if funding_rate is not None:
            indicators["funding_rate"] = funding_rate
            if funding_rate > self.config.funding_rate_threshold:
                score += 0.1
                reasons.append(
                    f"High funding rate ({funding_rate:.4f}) signals crowded longs"
                )

        # Determine signal
        confidence = min(1.0, score)
        indicators["composite_score"] = confidence

        if confidence >= 0.6:
            signal_type = BTCSignal.STRONG_SHORT
        elif confidence >= 0.35:
            signal_type = BTCSignal.SHORT
        else:
            signal_type = BTCSignal.NEUTRAL

        # Calculate stop loss and take profit for short
        stop_loss = current_price * (1 + self.config.stop_loss_pct) if signal_type != BTCSignal.NEUTRAL else None
        take_profit = current_price * (1 - self.config.take_profit_pct) if signal_type != BTCSignal.NEUTRAL else None

        signal = BTCShortSignal(
            signal=signal_type,
            confidence=confidence,
            entry_price=current_price if signal_type != BTCSignal.NEUTRAL else None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now(),
            reasons=reasons,
            indicators=indicators,
        )

        self.signal_history.append(signal)
        logger.info(
            f"BTC Short Signal: {signal_type.value} (confidence={confidence:.2f})"
        )
        return signal

    def should_close_short(
        self, prices: pd.Series, entry_price: float
    ) -> BTCShortSignal:
        """
        Check if an existing short position should be closed.

        Args:
            prices: Recent price data
            entry_price: The price at which the short was entered

        Returns:
            BTCShortSignal with CLOSE_SHORT or NEUTRAL
        """
        if len(prices) < self.config.rsi_period + 1:
            return BTCShortSignal(
                signal=BTCSignal.NEUTRAL,
                confidence=0.0,
                timestamp=datetime.now(),
                reasons=["Insufficient data"],
            )

        current_price = float(prices.iloc[-1])
        reasons = []
        close_score = 0.0

        # Stop loss hit
        stop_loss = entry_price * (1 + self.config.stop_loss_pct)
        if current_price >= stop_loss:
            return BTCShortSignal(
                signal=BTCSignal.CLOSE_SHORT,
                confidence=1.0,
                timestamp=datetime.now(),
                reasons=[f"Stop loss hit at {current_price:.2f} (stop: {stop_loss:.2f})"],
            )

        # Take profit hit
        take_profit = entry_price * (1 - self.config.take_profit_pct)
        if current_price <= take_profit:
            return BTCShortSignal(
                signal=BTCSignal.CLOSE_SHORT,
                confidence=1.0,
                timestamp=datetime.now(),
                reasons=[
                    f"Take profit hit at {current_price:.2f} (target: {take_profit:.2f})"
                ],
            )

        # RSI oversold = close short
        rsi = self.calculate_rsi(prices)
        current_rsi = float(rsi.iloc[-1])
        if current_rsi <= 30:
            close_score += 0.4
            reasons.append(f"RSI oversold at {current_rsi:.1f}")

        # MACD bullish crossover = close short
        macd_line, signal_line, _ = self.calculate_macd(prices)
        if float(macd_line.iloc[-1]) > float(signal_line.iloc[-1]) and float(
            macd_line.iloc[-2]
        ) <= float(signal_line.iloc[-2]):
            close_score += 0.3
            reasons.append("MACD bullish crossover")

        # EMA golden cross
        ema_short, ema_long = self.calculate_emas(prices)
        if float(ema_short.iloc[-1]) > float(ema_long.iloc[-1]) and float(
            ema_short.iloc[-2]
        ) <= float(ema_long.iloc[-2]):
            close_score += 0.3
            reasons.append("EMA golden cross (bullish reversal)")

        if close_score >= 0.5:
            return BTCShortSignal(
                signal=BTCSignal.CLOSE_SHORT,
                confidence=min(1.0, close_score),
                timestamp=datetime.now(),
                reasons=reasons,
            )

        return BTCShortSignal(
            signal=BTCSignal.NEUTRAL,
            confidence=0.0,
            timestamp=datetime.now(),
            reasons=["No close signal"],
        )
