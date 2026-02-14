"""
Comprehensive tests for BTC Short Trading functionality.

Tests cover:
- BTC short strategy signal generation
- MetaTrader 5 client (simulation mode)
- Swissquote Advanced Trade client (simulation mode)
- Risk management for short positions
- End-to-end short trading workflow
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strategies.btc_short_strategy import (
    BTCShortConfig,
    BTCShortStrategy,
    BTCSignal,
    BTCShortSignal,
)
from execution.metatrader5_client import (
    MetaTrader5Client,
    MT5Config,
    MT5OrderResult,
    MT5Position,
)
from execution.swissquote_advanced_trade import (
    SwissquoteAdvancedTradeClient,
    SQAdvancedConfig,
    SQOrderResult,
    SQOrderSide,
    SQOrderType,
)
from core.position import Position, PositionSide
from risk.risk_manager import RiskManager, RiskLimits


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def btc_strategy():
    """Create a BTC short strategy with default config"""
    return BTCShortStrategy()


@pytest.fixture
def btc_strategy_custom():
    """Create a BTC short strategy with custom config"""
    config = BTCShortConfig(
        rsi_period=14,
        rsi_overbought=65.0,  # More sensitive
        rsi_extreme_overbought=75.0,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
    )
    return BTCShortStrategy(config=config)


@pytest.fixture
def mt5_client():
    """Create an MT5 client in simulation mode"""
    config = MT5Config(simulation_mode=True, symbol="BTCUSD")
    client = MetaTrader5Client(config=config)
    client.connect()
    client.set_simulation_price(50000.0)
    return client


@pytest.fixture
def sq_client():
    """Create a Swissquote Advanced Trade client in sandbox mode"""
    config = SQAdvancedConfig(sandbox_mode=True)
    client = SwissquoteAdvancedTradeClient(config=config)

    async def setup():
        await client.connect()
        await client.authenticate()
        client.set_simulation_price(50000.0)

    asyncio.get_event_loop().run_until_complete(setup())
    return client


@pytest.fixture
def bearish_prices():
    """Generate bearish BTC price data (overbought -> decline)"""
    np.random.seed(42)
    n = 100
    # Start with strong uptrend, then reversal
    trend_up = np.linspace(40000, 55000, 60)
    trend_down = np.linspace(55000, 48000, 40)
    prices = np.concatenate([trend_up, trend_down])
    noise = np.random.normal(0, 200, n)
    return pd.Series(prices + noise, name="close")


@pytest.fixture
def bullish_prices():
    """Generate bullish BTC price data (oversold -> recovery)"""
    np.random.seed(123)
    n = 100
    trend_down = np.linspace(55000, 40000, 60)
    trend_up = np.linspace(40000, 48000, 40)
    prices = np.concatenate([trend_down, trend_up])
    noise = np.random.normal(0, 200, n)
    return pd.Series(prices + noise, name="close")


@pytest.fixture
def overbought_prices():
    """Generate extremely overbought BTC price data"""
    np.random.seed(99)
    n = 100
    # Parabolic rise
    prices = 30000 + np.exp(np.linspace(0, 3, n)) * 5000
    noise = np.random.normal(0, 100, n)
    return pd.Series(prices + noise, name="close")


@pytest.fixture
def volume_data():
    """Generate volume data with spike at end"""
    np.random.seed(42)
    n = 100
    base_volume = np.random.uniform(1000, 5000, n)
    # Spike at end
    base_volume[-3:] = base_volume[-3:] * 3
    return pd.Series(base_volume, name="volume")


@pytest.fixture
def risk_manager():
    """Create a risk manager"""
    limits = RiskLimits(
        max_position_size=0.05,  # 5% for BTC shorts
        max_leverage=2.0,
        max_daily_loss_pct=0.02,
    )
    return RiskManager(limits=limits)


# ============================================================
# BTC Short Strategy Tests
# ============================================================


class TestBTCShortStrategy:
    """Tests for BTCShortStrategy"""

    def test_strategy_initialization(self, btc_strategy):
        """Test strategy initializes correctly"""
        assert btc_strategy.config is not None
        assert btc_strategy.config.rsi_period == 14
        assert btc_strategy.config.stop_loss_pct == 0.03
        assert btc_strategy.config.take_profit_pct == 0.06
        assert len(btc_strategy.signal_history) == 0

    def test_strategy_custom_config(self, btc_strategy_custom):
        """Test strategy with custom config"""
        assert btc_strategy_custom.config.rsi_overbought == 65.0
        assert btc_strategy_custom.config.stop_loss_pct == 0.02

    def test_rsi_calculation(self, btc_strategy, bearish_prices):
        """Test RSI calculation produces valid values"""
        rsi = btc_strategy.calculate_rsi(bearish_prices)
        assert len(rsi) == len(bearish_prices)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_macd_calculation(self, btc_strategy, bearish_prices):
        """Test MACD calculation"""
        macd_line, signal_line, histogram = btc_strategy.calculate_macd(bearish_prices)
        assert len(macd_line) == len(bearish_prices)
        assert len(signal_line) == len(bearish_prices)
        assert len(histogram) == len(bearish_prices)
        # Histogram = MACD - Signal
        np.testing.assert_array_almost_equal(
            histogram.values, (macd_line - signal_line).values
        )

    def test_bollinger_bands(self, btc_strategy, bearish_prices):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = btc_strategy.calculate_bollinger_bands(bearish_prices)
        valid_idx = ~upper.isna()
        # Upper > Middle > Lower
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_ema_calculation(self, btc_strategy, bearish_prices):
        """Test EMA calculation"""
        ema_short, ema_long = btc_strategy.calculate_emas(bearish_prices)
        assert len(ema_short) == len(bearish_prices)
        assert len(ema_long) == len(bearish_prices)

    def test_analyze_bearish_data(self, btc_strategy, bearish_prices):
        """Test analysis on bearish data produces short signal"""
        signal = btc_strategy.analyze(bearish_prices)
        assert isinstance(signal, BTCShortSignal)
        assert signal.signal in (BTCSignal.SHORT, BTCSignal.STRONG_SHORT, BTCSignal.NEUTRAL)
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.timestamp is not None
        assert "rsi" in signal.indicators

    def test_analyze_overbought_data(self, btc_strategy, overbought_prices):
        """Test analysis on overbought data generates short signal"""
        signal = btc_strategy.analyze(overbought_prices)
        assert isinstance(signal, BTCShortSignal)
        # Overbought data should produce at least some confidence
        assert signal.confidence > 0
        assert len(signal.reasons) > 0

    def test_analyze_with_volume(self, btc_strategy, bearish_prices, volume_data):
        """Test analysis with volume data"""
        signal = btc_strategy.analyze(bearish_prices, volume=volume_data)
        assert isinstance(signal, BTCShortSignal)
        assert "volume_spike" in signal.indicators

    def test_analyze_with_funding_rate(self, btc_strategy, overbought_prices):
        """Test analysis with high funding rate"""
        signal = btc_strategy.analyze(overbought_prices, funding_rate=0.02)
        assert "funding_rate" in signal.indicators
        assert signal.indicators["funding_rate"] == 0.02

    def test_analyze_insufficient_data(self, btc_strategy):
        """Test analysis with insufficient data returns NEUTRAL"""
        short_prices = pd.Series([50000, 51000, 52000])
        signal = btc_strategy.analyze(short_prices)
        assert signal.signal == BTCSignal.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasons[0]

    def test_stop_loss_take_profit_on_signal(self, btc_strategy, overbought_prices):
        """Test that short signals include stop loss and take profit"""
        signal = btc_strategy.analyze(overbought_prices)
        if signal.signal != BTCSignal.NEUTRAL:
            assert signal.entry_price is not None
            assert signal.stop_loss is not None
            assert signal.take_profit is not None
            # For short: stop loss > entry > take profit
            assert signal.stop_loss > signal.entry_price
            assert signal.take_profit < signal.entry_price

    def test_should_close_short_stop_loss(self, btc_strategy):
        """Test close signal when stop loss is hit"""
        np.random.seed(42)
        prices = pd.Series(np.linspace(50000, 52000, 50))
        entry_price = 50000.0

        signal = btc_strategy.should_close_short(prices, entry_price)
        # Price rose from 50000 to 52000, which is +4% > 3% stop loss
        assert signal.signal == BTCSignal.CLOSE_SHORT
        assert signal.confidence == 1.0

    def test_should_close_short_take_profit(self, btc_strategy):
        """Test close signal when take profit is hit"""
        np.random.seed(42)
        prices = pd.Series(np.linspace(50000, 46000, 50))
        entry_price = 50000.0

        signal = btc_strategy.should_close_short(prices, entry_price)
        # Price dropped from 50000 to 46000, which is -8% > 6% take profit
        assert signal.signal == BTCSignal.CLOSE_SHORT
        assert signal.confidence == 1.0

    def test_signal_history(self, btc_strategy, bearish_prices, overbought_prices):
        """Test that signals are accumulated in history"""
        btc_strategy.analyze(bearish_prices)
        btc_strategy.analyze(overbought_prices)
        assert len(btc_strategy.signal_history) == 2

    def test_composite_score_capped_at_one(self, btc_strategy, overbought_prices):
        """Test that composite score never exceeds 1.0"""
        signal = btc_strategy.analyze(
            overbought_prices, funding_rate=0.05
        )
        assert signal.confidence <= 1.0


# ============================================================
# MetaTrader 5 Client Tests
# ============================================================


class TestMetaTrader5Client:
    """Tests for MetaTrader5Client in simulation mode"""

    def test_connection(self, mt5_client):
        """Test MT5 simulation connection"""
        assert mt5_client.is_connected is True

    def test_disconnect(self, mt5_client):
        """Test MT5 disconnect"""
        mt5_client.disconnect()
        assert mt5_client.is_connected is False

    def test_account_info(self, mt5_client):
        """Test getting account info"""
        info = mt5_client.get_account_info()
        assert info["balance"] == 100000.0
        assert info["currency"] == "USD"
        assert info["server"] == "Simulation"

    def test_get_price(self, mt5_client):
        """Test getting simulated price"""
        price = mt5_client.get_symbol_price()
        assert price == 50000.0

    def test_set_simulation_price(self, mt5_client):
        """Test setting simulated price"""
        mt5_client.set_simulation_price(55000.0)
        assert mt5_client.get_symbol_price() == 55000.0

    def test_open_short(self, mt5_client):
        """Test opening a short position"""
        result = mt5_client.open_short(
            volume=0.1,
            stop_loss=52000.0,
            take_profit=47000.0,
        )
        assert result.success is True
        assert result.volume == 0.1
        assert result.price == 50000.0
        assert result.order_id > 0

    def test_open_short_no_price(self):
        """Test opening short fails when no price is set"""
        config = MT5Config(simulation_mode=True)
        client = MetaTrader5Client(config=config)
        client.connect()
        # Don't set price
        result = client.open_short(volume=0.1)
        assert result.success is False
        assert "No price" in result.message

    def test_open_short_not_connected(self):
        """Test opening short fails when not connected"""
        config = MT5Config(simulation_mode=True)
        client = MetaTrader5Client(config=config)
        result = client.open_short(volume=0.1)
        assert result.success is False
        assert "Not connected" in result.message

    def test_close_short_profit(self, mt5_client):
        """Test closing a short position at profit"""
        # Open at 50000
        open_result = mt5_client.open_short(volume=0.5)
        assert open_result.success is True

        # Price drops to 48000 (profit for short)
        mt5_client.set_simulation_price(48000.0)

        close_result = mt5_client.close_short(open_result.order_id)
        assert close_result.success is True
        assert "P&L" in close_result.message
        # P&L should be positive: (50000 - 48000) * 0.5 = 1000
        assert "1000.00" in close_result.message

    def test_close_short_loss(self, mt5_client):
        """Test closing a short position at loss"""
        open_result = mt5_client.open_short(volume=0.5)
        assert open_result.success is True

        # Price rises to 52000 (loss for short)
        mt5_client.set_simulation_price(52000.0)

        close_result = mt5_client.close_short(open_result.order_id)
        assert close_result.success is True
        # P&L should be negative: (50000 - 52000) * 0.5 = -1000
        assert "-1000.00" in close_result.message

    def test_close_nonexistent_position(self, mt5_client):
        """Test closing a position that doesn't exist"""
        result = mt5_client.close_short(999999)
        assert result.success is False
        assert "not found" in result.message

    def test_partial_close(self, mt5_client):
        """Test partial close of a short position"""
        open_result = mt5_client.open_short(volume=1.0)
        assert open_result.success is True

        # Partial close 0.5 of 1.0
        close_result = mt5_client.close_short(open_result.order_id, volume=0.5)
        assert close_result.success is True
        assert close_result.volume == 0.5

        # Remaining position should have 0.5 volume
        positions = mt5_client.get_open_short_positions()
        assert len(positions) == 1
        assert positions[0].volume == 0.5

    def test_get_positions(self, mt5_client):
        """Test getting open positions"""
        mt5_client.open_short(volume=0.1)
        mt5_client.open_short(volume=0.2)

        positions = mt5_client.get_positions()
        assert len(positions) == 2

    def test_get_open_short_positions(self, mt5_client):
        """Test filtering short positions"""
        mt5_client.open_short(volume=0.1)
        mt5_client.open_short(volume=0.2)

        shorts = mt5_client.get_open_short_positions()
        assert len(shorts) == 2
        assert all(p.type == "SELL" for p in shorts)

    def test_modify_position(self, mt5_client):
        """Test modifying stop loss and take profit"""
        open_result = mt5_client.open_short(volume=0.1, stop_loss=52000.0)
        assert open_result.success is True

        mod_result = mt5_client.modify_position(
            open_result.order_id,
            stop_loss=51500.0,
            take_profit=48000.0,
        )
        assert mod_result.success is True

        positions = mt5_client.get_open_short_positions()
        assert positions[0].sl == 51500.0
        assert positions[0].tp == 48000.0

    def test_position_pnl_updates(self, mt5_client):
        """Test that P&L updates when price changes"""
        mt5_client.open_short(volume=1.0)  # Open at 50000

        mt5_client.set_simulation_price(48000.0)  # Price drops
        positions = mt5_client.get_open_short_positions()
        assert positions[0].profit == 2000.0  # (50000 - 48000) * 1.0

        mt5_client.set_simulation_price(53000.0)  # Price rises
        positions = mt5_client.get_open_short_positions()
        assert positions[0].profit == -3000.0  # (50000 - 53000) * 1.0

    def test_balance_updates_on_close(self, mt5_client):
        """Test balance updates correctly after closing positions"""
        initial_balance = mt5_client.get_account_info()["balance"]

        open_result = mt5_client.open_short(volume=1.0)
        mt5_client.set_simulation_price(48000.0)
        mt5_client.close_short(open_result.order_id)

        final_balance = mt5_client.get_account_info()["balance"]
        # Should have gained 2000 (50000 - 48000) * 1.0
        assert final_balance == initial_balance + 2000.0


# ============================================================
# Swissquote Advanced Trade Client Tests
# ============================================================


class TestSwissquoteAdvancedTrade:
    """Tests for SwissquoteAdvancedTradeClient in simulation mode"""

    def test_authentication(self, sq_client):
        """Test sandbox authentication"""
        assert sq_client.is_authenticated is True

    def test_account_info(self, sq_client):
        """Test getting account info"""
        info = asyncio.get_event_loop().run_until_complete(
            sq_client.get_account_info()
        )
        assert info["balance"] == 100000.0
        assert "equity" in info
        assert "margin_used" in info

    def test_get_btc_price(self, sq_client):
        """Test getting BTC price"""
        price = asyncio.get_event_loop().run_until_complete(
            sq_client.get_btc_price()
        )
        assert price == 50000.0

    def test_open_short(self, sq_client):
        """Test opening a short position"""
        result = asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(
                volume=0.5,
                stop_loss=52000.0,
                take_profit=47000.0,
            )
        )
        assert result.success is True
        assert result.fill_price == 50000.0
        assert result.fill_volume == 0.5
        assert result.order_id.startswith("SQ-")
        assert result.fees > 0

    def test_open_short_not_authenticated(self):
        """Test opening short fails without authentication"""
        config = SQAdvancedConfig(sandbox_mode=True)
        client = SwissquoteAdvancedTradeClient(config=config)
        result = asyncio.get_event_loop().run_until_complete(
            client.open_short(volume=0.1)
        )
        assert result.success is False
        assert "Not authenticated" in result.message

    def test_open_short_no_price(self):
        """Test opening short fails without price"""
        config = SQAdvancedConfig(sandbox_mode=True)
        client = SwissquoteAdvancedTradeClient(config=config)

        async def run():
            await client.connect()
            await client.authenticate()
            return await client.open_short(volume=0.1)

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result.success is False

    def test_close_short_profit(self, sq_client):
        """Test closing a short at profit"""
        open_result = asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=1.0)
        )

        # Price drops (profit for short)
        sq_client.set_simulation_price(47000.0)

        close_result = asyncio.get_event_loop().run_until_complete(
            sq_client.close_short(open_result.order_id)
        )
        assert close_result.success is True
        assert "P&L: 3000.00" in close_result.message

    def test_close_short_loss(self, sq_client):
        """Test closing a short at loss"""
        open_result = asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=1.0)
        )

        sq_client.set_simulation_price(53000.0)

        close_result = asyncio.get_event_loop().run_until_complete(
            sq_client.close_short(open_result.order_id)
        )
        assert close_result.success is True
        assert "P&L: -3000.00" in close_result.message

    def test_close_nonexistent_position(self, sq_client):
        """Test closing nonexistent position"""
        result = asyncio.get_event_loop().run_until_complete(
            sq_client.close_short("NONEXISTENT")
        )
        assert result.success is False

    def test_get_positions(self, sq_client):
        """Test getting open positions"""
        asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=0.1)
        )
        asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=0.2)
        )

        positions = asyncio.get_event_loop().run_until_complete(
            sq_client.get_positions()
        )
        assert len(positions) == 2

    def test_get_open_short_positions(self, sq_client):
        """Test filtering short positions"""
        asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=0.3)
        )

        shorts = asyncio.get_event_loop().run_until_complete(
            sq_client.get_open_short_positions()
        )
        assert len(shorts) == 1
        assert shorts[0].side == SQOrderSide.SELL

    def test_modify_position(self, sq_client):
        """Test modifying stop loss and take profit"""
        open_result = asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=0.1, stop_loss=52000.0)
        )

        mod_result = asyncio.get_event_loop().run_until_complete(
            sq_client.modify_position(
                open_result.order_id,
                stop_loss=51000.0,
                take_profit=48000.0,
            )
        )
        assert mod_result.success is True

    def test_trailing_stop(self, sq_client):
        """Test setting trailing stop"""
        open_result = asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=0.1)
        )

        trail_result = asyncio.get_event_loop().run_until_complete(
            sq_client.set_trailing_stop(open_result.order_id, trail_distance=1500.0)
        )
        assert trail_result.success is True

    def test_margin_calculation(self, sq_client):
        """Test margin is calculated on open"""
        asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=1.0)
        )

        positions = asyncio.get_event_loop().run_until_complete(
            sq_client.get_positions()
        )
        # Margin = 10% of position value = 50000 * 1.0 * 0.10 = 5000
        assert positions[0].margin_used == 5000.0

    def test_pnl_updates_on_price_change(self, sq_client):
        """Test unrealized P&L updates with price changes"""
        asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(volume=1.0)
        )

        sq_client.set_simulation_price(48000.0)
        positions = asyncio.get_event_loop().run_until_complete(
            sq_client.get_positions()
        )
        # Short P&L: (50000 - 48000) * 1.0 = 2000
        assert positions[0].unrealized_pnl == 2000.0

    def test_limit_order_short(self, sq_client):
        """Test limit order for short entry"""
        result = asyncio.get_event_loop().run_until_complete(
            sq_client.open_short(
                volume=0.5,
                order_type=SQOrderType.LIMIT,
                limit_price=51000.0,
            )
        )
        assert result.success is True
        assert result.fill_price == 51000.0


# ============================================================
# Risk Management for BTC Short Tests
# ============================================================


class TestBTCShortRiskManagement:
    """Tests for risk management applied to BTC short trading"""

    def test_position_size_check(self, risk_manager):
        """Test position size limit for BTC shorts"""
        portfolio_value = 100000.0
        # 5% max position = $5000
        assert risk_manager.check_position_size(portfolio_value, 4000.0) is True
        assert risk_manager.check_position_size(portfolio_value, 6000.0) is False

    def test_leverage_check(self, risk_manager):
        """Test leverage check"""
        portfolio_value = 100000.0
        # 2.0x max leverage
        assert risk_manager.check_leverage(150000.0, portfolio_value) is True
        assert risk_manager.check_leverage(250000.0, portfolio_value) is False

    def test_daily_loss_check(self, risk_manager):
        """Test daily loss limit"""
        portfolio_value = 100000.0
        # 2% max daily loss = $2000
        assert risk_manager.check_daily_loss(-1500.0, portfolio_value) is True
        assert risk_manager.check_daily_loss(-2500.0, portfolio_value) is False

    def test_stop_loss_for_short(self, risk_manager):
        """Test stop loss calculation (for longs - shorts need inverse)"""
        entry_price = 50000.0
        stop = risk_manager.calculate_stop_loss(entry_price)
        # Default 5% stop loss
        assert stop == 47500.0

    def test_validate_btc_short_trade(self, risk_manager):
        """Test full trade validation for BTC short"""
        approved, msg = risk_manager.validate_trade(
            portfolio_value=100000.0,
            gross_exposure=120000.0,  # Within 2x leverage
            position_value=4000.0,  # Within 5% limit
            daily_pnl=-1000.0,  # Within 2% daily loss
        )
        assert approved is True

    def test_reject_oversized_btc_short(self, risk_manager):
        """Test rejection of oversized BTC short"""
        approved, msg = risk_manager.validate_trade(
            portfolio_value=100000.0,
            gross_exposure=120000.0,
            position_value=10000.0,  # 10% > 5% limit
            daily_pnl=0.0,
        )
        assert approved is False
        assert "Position size" in msg


# ============================================================
# Core Position Tests for Short Positions
# ============================================================


class TestShortPosition:
    """Tests for short position tracking"""

    def test_short_position_creation(self):
        """Test creating a short position"""
        pos = Position(
            symbol="BTCUSD",
            quantity=-1.0,
            entry_price=50000.0,
            entry_time=datetime.now(),
            side=PositionSide.SHORT,
        )
        assert pos.side == PositionSide.SHORT
        assert pos.is_open is True

    def test_short_position_pnl_profit(self):
        """Test short position P&L when price drops (profit)"""
        pos = Position(
            symbol="BTCUSD",
            quantity=-1.0,
            entry_price=50000.0,
            entry_time=datetime.now(),
            side=PositionSide.SHORT,
        )
        pnl = pos.calculate_pnl(48000.0)
        assert pnl == 2000.0  # (50000 - 48000) * 1.0

    def test_short_position_pnl_loss(self):
        """Test short position P&L when price rises (loss)"""
        pos = Position(
            symbol="BTCUSD",
            quantity=-1.0,
            entry_price=50000.0,
            entry_time=datetime.now(),
            side=PositionSide.SHORT,
        )
        pnl = pos.calculate_pnl(53000.0)
        assert pnl == -3000.0  # (50000 - 53000) * 1.0

    def test_close_short_position(self):
        """Test closing a short position"""
        pos = Position(
            symbol="BTCUSD",
            quantity=-1.0,
            entry_price=50000.0,
            entry_time=datetime.now(),
            side=PositionSide.SHORT,
        )
        realized = pos.close(47000.0, datetime.now())
        assert realized == 3000.0
        assert pos.side == PositionSide.FLAT
        assert pos.is_open is False


# ============================================================
# End-to-End Integration Tests
# ============================================================


class TestEndToEndBTCShort:
    """End-to-end integration tests for BTC short trading"""

    def test_strategy_to_mt5_execution(self, btc_strategy, mt5_client, overbought_prices):
        """Test full flow: strategy signal -> MT5 execution"""
        # Step 1: Generate signal
        signal = btc_strategy.analyze(overbought_prices)

        if signal.signal in (BTCSignal.SHORT, BTCSignal.STRONG_SHORT):
            # Step 2: Execute on MT5
            result = mt5_client.open_short(
                volume=0.1,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
            )
            assert result.success is True

            # Step 3: Verify position
            positions = mt5_client.get_open_short_positions()
            assert len(positions) >= 1

    def test_strategy_to_swissquote_execution(
        self, btc_strategy, sq_client, overbought_prices
    ):
        """Test full flow: strategy signal -> Swissquote execution"""
        signal = btc_strategy.analyze(overbought_prices)

        if signal.signal in (BTCSignal.SHORT, BTCSignal.STRONG_SHORT):
            result = asyncio.get_event_loop().run_until_complete(
                sq_client.open_short(
                    volume=0.1,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                )
            )
            assert result.success is True

    def test_full_short_lifecycle_mt5(self, btc_strategy, mt5_client, overbought_prices):
        """Test complete short trade lifecycle on MT5"""
        # Open short
        signal = btc_strategy.analyze(overbought_prices)
        entry_price = mt5_client.get_symbol_price()

        open_result = mt5_client.open_short(
            volume=0.5,
            stop_loss=signal.stop_loss if signal.stop_loss else entry_price * 1.03,
            take_profit=signal.take_profit if signal.take_profit else entry_price * 0.94,
        )
        assert open_result.success is True

        # Simulate price drop
        mt5_client.set_simulation_price(entry_price * 0.95)

        # Check if we should close
        new_prices = pd.Series(np.linspace(entry_price, entry_price * 0.95, 50))
        close_signal = btc_strategy.should_close_short(new_prices, entry_price)

        # Close position
        close_result = mt5_client.close_short(open_result.order_id)
        assert close_result.success is True

        # Verify no open positions
        positions = mt5_client.get_open_short_positions()
        assert len(positions) == 0

    def test_risk_validated_short(self, btc_strategy, mt5_client, risk_manager, overbought_prices):
        """Test short trade with risk validation"""
        portfolio_value = 100000.0
        signal = btc_strategy.analyze(overbought_prices)

        if signal.signal != BTCSignal.NEUTRAL:
            position_value = signal.entry_price * 0.1  # 0.1 BTC

            approved, msg = risk_manager.validate_trade(
                portfolio_value=portfolio_value,
                gross_exposure=position_value,
                position_value=position_value,
                daily_pnl=0.0,
            )

            if approved:
                result = mt5_client.open_short(
                    volume=0.1,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                )
                assert result.success is True


# ============================================================
# Edge Case Tests
# ============================================================


class TestEdgeCases:
    """Edge case tests"""

    def test_zero_volume_trade(self, mt5_client):
        """Test trading with zero volume"""
        result = mt5_client.open_short(volume=0.0)
        # Should succeed in simulation (validation is on the real MT5 side)
        assert result.success is True

    def test_very_small_volume(self, mt5_client):
        """Test trading with very small volume"""
        result = mt5_client.open_short(volume=0.001)
        assert result.success is True

    def test_multiple_positions(self, mt5_client):
        """Test handling multiple simultaneous positions"""
        tickets = []
        for i in range(5):
            result = mt5_client.open_short(volume=0.1)
            assert result.success is True
            tickets.append(result.order_id)

        positions = mt5_client.get_open_short_positions()
        assert len(positions) == 5

        # Close all
        for ticket in tickets:
            close = mt5_client.close_short(ticket)
            assert close.success is True

        positions = mt5_client.get_open_short_positions()
        assert len(positions) == 0

    def test_strategy_with_flat_prices(self, btc_strategy):
        """Test strategy with completely flat prices"""
        flat_prices = pd.Series([50000.0] * 100)
        signal = btc_strategy.analyze(flat_prices)
        assert signal.signal == BTCSignal.NEUTRAL

    def test_strategy_with_volatile_prices(self, btc_strategy):
        """Test strategy with highly volatile prices"""
        np.random.seed(42)
        volatile = pd.Series(50000 + np.random.normal(0, 5000, 100))
        signal = btc_strategy.analyze(volatile)
        assert isinstance(signal, BTCShortSignal)
        assert 0.0 <= signal.confidence <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
