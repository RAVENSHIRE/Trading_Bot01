"""
Swissquote Advanced Trade Integration for BTC Short Trading

Extends the base Swissquote client with Advanced Trade features:
- CFD/Crypto margin trading
- BTC short selling via CFD
- Margin management
- Advanced order types (trailing stops, OCO)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)


class SQOrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class SQOrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"


class SQInstrumentType(Enum):
    CFD = "CFD"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"


@dataclass
class SQAdvancedConfig:
    """Swissquote Advanced Trade configuration"""
    api_key: str = ""
    api_secret: str = ""
    account_id: str = ""
    base_url: str = "https://trade.swissquote.ch/api/v2"
    sandbox_mode: bool = True
    default_currency: str = "USD"
    btc_symbol: str = "BTCUSD"
    instrument_type: SQInstrumentType = SQInstrumentType.CFD


@dataclass
class SQPosition:
    """Swissquote position"""
    position_id: str
    symbol: str
    side: SQOrderSide
    volume: float
    open_price: float
    current_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    unrealized_pnl: float
    margin_used: float
    open_time: datetime


@dataclass
class SQOrderResult:
    """Result of an order operation"""
    success: bool
    order_id: str = ""
    fill_price: float = 0.0
    fill_volume: float = 0.0
    message: str = ""
    fees: float = 0.0


class SwissquoteAdvancedTradeClient:
    """
    Swissquote Advanced Trade client for BTC CFD/crypto short trading.

    Supports both real API calls and simulation mode for testing.
    """

    def __init__(self, config: Optional[SQAdvancedConfig] = None):
        self.config = config or SQAdvancedConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._authenticated = False

        # Simulation state
        self._sim_mode = self.config.sandbox_mode
        self._sim_positions: Dict[str, SQPosition] = {}
        self._sim_next_id = 1
        self._sim_balance = 100000.0
        self._sim_price = 0.0

        logger.info(
            f"Swissquote Advanced Trade client initialized "
            f"(sandbox={self.config.sandbox_mode})"
        )

    async def connect(self) -> None:
        """Establish HTTP session"""
        self.session = aiohttp.ClientSession(
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        logger.info("Swissquote Advanced Trade session created")

    async def disconnect(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Swissquote Advanced Trade session closed")

    async def authenticate(self) -> bool:
        """Authenticate with Swissquote Advanced Trade API"""
        if self._sim_mode:
            self._authenticated = True
            logger.info("Swissquote Advanced Trade authenticated (simulation)")
            return True

        if not self.session:
            await self.connect()

        try:
            async with self.session.post(
                f"{self.config.base_url}/auth/token",
                json={
                    "api_key": self.config.api_key,
                    "api_secret": self.config.api_secret,
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.session.headers.update(
                        {"Authorization": f"Bearer {data.get('access_token', '')}"}
                    )
                    self._authenticated = True
                    logger.info("Swissquote Advanced Trade authenticated")
                    return True
                logger.error(f"Authentication failed: {response.status}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    def set_simulation_price(self, price: float) -> None:
        """Set simulated BTC price"""
        self._sim_price = price
        for pos in self._sim_positions.values():
            pos.current_price = price
            if pos.side == SQOrderSide.SELL:
                pos.unrealized_pnl = (pos.open_price - price) * pos.volume
            else:
                pos.unrealized_pnl = (price - pos.open_price) * pos.volume

    async def get_account_info(self) -> Dict:
        """Get account information"""
        if self._sim_mode:
            total_pnl = sum(p.unrealized_pnl for p in self._sim_positions.values())
            total_margin = sum(p.margin_used for p in self._sim_positions.values())
            return {
                "account_id": self.config.account_id or "SIM-001",
                "balance": self._sim_balance,
                "equity": self._sim_balance + total_pnl,
                "margin_used": total_margin,
                "margin_available": self._sim_balance + total_pnl - total_margin,
                "currency": self.config.default_currency,
                "platform": "Advanced Trade (Simulation)",
            }

        try:
            async with self.session.get(
                f"{self.config.base_url}/accounts/{self.config.account_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}

    async def get_btc_price(self) -> Optional[float]:
        """Get current BTC price"""
        if self._sim_mode:
            return self._sim_price if self._sim_price > 0 else None

        try:
            async with self.session.get(
                f"{self.config.base_url}/quotes/{self.config.btc_symbol}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("bid")
                return None
        except Exception as e:
            logger.error(f"Error getting BTC price: {e}")
            return None

    async def open_short(
        self,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_type: SQOrderType = SQOrderType.MARKET,
        limit_price: Optional[float] = None,
    ) -> SQOrderResult:
        """
        Open a BTC short position via CFD.

        Args:
            volume: Position size in BTC
            stop_loss: Stop loss price
            take_profit: Take profit price
            order_type: Order type (MARKET, LIMIT, etc.)
            limit_price: Limit price (for LIMIT orders)

        Returns:
            SQOrderResult
        """
        if not self._authenticated:
            return SQOrderResult(success=False, message="Not authenticated")

        if self._sim_mode:
            if self._sim_price <= 0:
                return SQOrderResult(
                    success=False, message="No price available in simulation"
                )

            fill_price = self._sim_price
            if order_type == SQOrderType.LIMIT and limit_price:
                if limit_price < self._sim_price:
                    return SQOrderResult(
                        success=False,
                        message="Limit price below market for short entry",
                    )
                fill_price = limit_price

            position_id = f"SQ-{self._sim_next_id:06d}"
            self._sim_next_id += 1

            # Margin requirement: ~10% of position value for BTC CFD
            margin = fill_price * volume * 0.10
            fees = fill_price * volume * 0.001  # 0.1% fee

            position = SQPosition(
                position_id=position_id,
                symbol=self.config.btc_symbol,
                side=SQOrderSide.SELL,
                volume=volume,
                open_price=fill_price,
                current_price=fill_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                unrealized_pnl=0.0,
                margin_used=margin,
                open_time=datetime.now(),
            )
            self._sim_positions[position_id] = position
            self._sim_balance -= fees

            logger.info(
                f"SQ SIM: Opened short {volume} BTC @ {fill_price} "
                f"(SL={stop_loss}, TP={take_profit}, margin={margin:.2f})"
            )
            return SQOrderResult(
                success=True,
                order_id=position_id,
                fill_price=fill_price,
                fill_volume=volume,
                message="Short position opened",
                fees=fees,
            )

        # Real API call
        order_data = {
            "symbol": self.config.btc_symbol,
            "side": SQOrderSide.SELL.value,
            "volume": volume,
            "order_type": order_type.value,
            "instrument_type": self.config.instrument_type.value,
            "account_id": self.config.account_id,
        }
        if stop_loss:
            order_data["stop_loss"] = stop_loss
        if take_profit:
            order_data["take_profit"] = take_profit
        if limit_price and order_type in (SQOrderType.LIMIT, SQOrderType.STOP_LIMIT):
            order_data["price"] = limit_price

        try:
            async with self.session.post(
                f"{self.config.base_url}/orders", json=order_data
            ) as response:
                if response.status in (200, 201):
                    data = await response.json()
                    return SQOrderResult(
                        success=True,
                        order_id=data.get("order_id", ""),
                        fill_price=data.get("fill_price", 0.0),
                        fill_volume=data.get("fill_volume", volume),
                        message="Order placed",
                        fees=data.get("fees", 0.0),
                    )
                error = await response.text()
                return SQOrderResult(
                    success=False, message=f"Order failed: {response.status} - {error}"
                )
        except Exception as e:
            logger.error(f"Error placing short order: {e}")
            return SQOrderResult(success=False, message=str(e))

    async def close_short(
        self,
        position_id: str,
        volume: Optional[float] = None,
    ) -> SQOrderResult:
        """
        Close a short position by buying back.

        Args:
            position_id: ID of the position to close
            volume: Partial close volume (None = full close)

        Returns:
            SQOrderResult
        """
        if not self._authenticated:
            return SQOrderResult(success=False, message="Not authenticated")

        if self._sim_mode:
            if position_id not in self._sim_positions:
                return SQOrderResult(
                    success=False, message=f"Position {position_id} not found"
                )

            pos = self._sim_positions[position_id]
            close_vol = volume or pos.volume
            close_price = self._sim_price

            realized_pnl = (pos.open_price - close_price) * close_vol
            fees = close_price * close_vol * 0.001
            self._sim_balance += realized_pnl - fees

            if close_vol >= pos.volume:
                del self._sim_positions[position_id]
            else:
                pos.volume -= close_vol
                pos.unrealized_pnl = (pos.open_price - close_price) * pos.volume

            logger.info(
                f"SQ SIM: Closed short {close_vol} BTC @ {close_price} "
                f"(P&L={realized_pnl:.2f})"
            )
            return SQOrderResult(
                success=True,
                order_id=position_id,
                fill_price=close_price,
                fill_volume=close_vol,
                message=f"Position closed, P&L: {realized_pnl:.2f}",
                fees=fees,
            )

        # Real API call
        try:
            close_data = {
                "position_id": position_id,
                "account_id": self.config.account_id,
            }
            if volume:
                close_data["volume"] = volume

            async with self.session.post(
                f"{self.config.base_url}/positions/{position_id}/close",
                json=close_data,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return SQOrderResult(
                        success=True,
                        order_id=position_id,
                        fill_price=data.get("fill_price", 0.0),
                        fill_volume=data.get("fill_volume", 0.0),
                        message="Position closed",
                        fees=data.get("fees", 0.0),
                    )
                error = await response.text()
                return SQOrderResult(
                    success=False,
                    message=f"Close failed: {response.status} - {error}",
                )
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return SQOrderResult(success=False, message=str(e))

    async def get_positions(self) -> List[SQPosition]:
        """Get all open positions"""
        if self._sim_mode:
            return list(self._sim_positions.values())

        try:
            async with self.session.get(
                f"{self.config.base_url}/accounts/{self.config.account_id}/positions"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        SQPosition(
                            position_id=p["position_id"],
                            symbol=p["symbol"],
                            side=SQOrderSide(p["side"]),
                            volume=p["volume"],
                            open_price=p["open_price"],
                            current_price=p.get("current_price", 0.0),
                            stop_loss=p.get("stop_loss"),
                            take_profit=p.get("take_profit"),
                            unrealized_pnl=p.get("unrealized_pnl", 0.0),
                            margin_used=p.get("margin_used", 0.0),
                            open_time=datetime.fromisoformat(p["open_time"]),
                        )
                        for p in data
                    ]
                return []
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    async def get_open_short_positions(self) -> List[SQPosition]:
        """Get all open short positions for BTC"""
        positions = await self.get_positions()
        return [
            p
            for p in positions
            if p.side == SQOrderSide.SELL and p.symbol == self.config.btc_symbol
        ]

    async def modify_position(
        self,
        position_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> SQOrderResult:
        """Modify stop loss / take profit on an existing position"""
        if not self._authenticated:
            return SQOrderResult(success=False, message="Not authenticated")

        if self._sim_mode:
            if position_id not in self._sim_positions:
                return SQOrderResult(
                    success=False, message=f"Position {position_id} not found"
                )
            pos = self._sim_positions[position_id]
            if stop_loss is not None:
                pos.stop_loss = stop_loss
            if take_profit is not None:
                pos.take_profit = take_profit
            return SQOrderResult(
                success=True,
                order_id=position_id,
                message="Position modified",
            )

        try:
            modify_data = {}
            if stop_loss is not None:
                modify_data["stop_loss"] = stop_loss
            if take_profit is not None:
                modify_data["take_profit"] = take_profit

            async with self.session.put(
                f"{self.config.base_url}/positions/{position_id}",
                json=modify_data,
            ) as response:
                if response.status == 200:
                    return SQOrderResult(
                        success=True,
                        order_id=position_id,
                        message="Position modified",
                    )
                error = await response.text()
                return SQOrderResult(
                    success=False,
                    message=f"Modify failed: {response.status} - {error}",
                )
        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return SQOrderResult(success=False, message=str(e))

    async def set_trailing_stop(
        self,
        position_id: str,
        trail_distance: float,
    ) -> SQOrderResult:
        """
        Set a trailing stop on a position.

        Args:
            position_id: Position to modify
            trail_distance: Distance in price units to trail
        """
        if not self._authenticated:
            return SQOrderResult(success=False, message="Not authenticated")

        if self._sim_mode:
            if position_id not in self._sim_positions:
                return SQOrderResult(
                    success=False, message=f"Position {position_id} not found"
                )
            pos = self._sim_positions[position_id]
            # For short: trailing stop is above current price
            pos.stop_loss = pos.current_price + trail_distance
            return SQOrderResult(
                success=True,
                order_id=position_id,
                message=f"Trailing stop set at {pos.stop_loss:.2f}",
            )

        try:
            async with self.session.post(
                f"{self.config.base_url}/positions/{position_id}/trailing-stop",
                json={"trail_distance": trail_distance},
            ) as response:
                if response.status == 200:
                    return SQOrderResult(
                        success=True,
                        order_id=position_id,
                        message="Trailing stop set",
                    )
                error = await response.text()
                return SQOrderResult(
                    success=False,
                    message=f"Trailing stop failed: {response.status} - {error}",
                )
        except Exception as e:
            logger.error(f"Error setting trailing stop: {e}")
            return SQOrderResult(success=False, message=str(e))
