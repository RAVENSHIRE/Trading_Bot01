"""
MetaTrader 5 Integration for BTC Short Trading

Provides a client for connecting to MetaTrader 5 to execute BTC CFD short
trades. Supports both live MT5 connections (via MetaTrader5 Python package)
and a simulation mode for testing without a broker connection.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MT5OrderType(Enum):
    """MT5 order types"""
    MARKET_BUY = 0
    MARKET_SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5


class MT5TradeAction(Enum):
    """MT5 trade actions"""
    DEAL = "DEAL"
    PENDING = "PENDING"
    MODIFY = "MODIFY"
    REMOVE = "REMOVE"


@dataclass
class MT5Config:
    """MetaTrader 5 connection configuration"""
    server: str = ""
    login: int = 0
    password: str = ""
    timeout: int = 10000
    symbol: str = "BTCUSD"
    magic_number: int = 234000  # Unique identifier for bot orders
    deviation: int = 20  # Max price deviation in points
    filling_type: int = 1  # IOC filling
    simulation_mode: bool = True  # Use simulation when MT5 not available


@dataclass
class MT5Position:
    """Represents an MT5 position"""
    ticket: int
    symbol: str
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    time: datetime
    type: str  # "BUY" or "SELL"
    magic: int = 0


@dataclass
class MT5OrderResult:
    """Result of an MT5 order operation"""
    success: bool
    order_id: int = 0
    volume: float = 0.0
    price: float = 0.0
    message: str = ""
    retcode: int = 0


class MetaTrader5Client:
    """
    MetaTrader 5 client for BTC CFD trading.

    Supports both real MT5 connections and simulation mode.
    In simulation mode, tracks positions internally for testing.
    """

    def __init__(self, config: Optional[MT5Config] = None):
        self.config = config or MT5Config()
        self._connected = False
        self._mt5 = None
        self._simulation = self.config.simulation_mode

        # Simulation state
        self._sim_positions: Dict[int, MT5Position] = {}
        self._sim_next_ticket = 100001
        self._sim_balance = 100000.0
        self._sim_equity = 100000.0
        self._sim_price = 0.0  # Current simulated BTC price

        logger.info(
            f"MT5 client initialized (simulation={self._simulation}, "
            f"symbol={self.config.symbol})"
        )

    def connect(self) -> bool:
        """Connect to MetaTrader 5 terminal"""
        if self._simulation:
            self._connected = True
            logger.info("MT5 simulation mode connected")
            return True

        try:
            import MetaTrader5 as mt5

            self._mt5 = mt5

            if not mt5.initialize(
                login=self.config.login,
                server=self.config.server,
                password=self.config.password,
                timeout=self.config.timeout,
            ):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False

            self._connected = True
            account_info = mt5.account_info()
            if account_info:
                logger.info(
                    f"MT5 connected: account={account_info.login}, "
                    f"balance={account_info.balance}, server={account_info.server}"
                )
            return True

        except ImportError:
            logger.warning("MetaTrader5 package not installed, falling back to simulation")
            self._simulation = True
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MetaTrader 5"""
        if not self._simulation and self._mt5:
            self._mt5.shutdown()
        self._connected = False
        logger.info("MT5 disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_account_info(self) -> Dict:
        """Get account information"""
        if not self._connected:
            return {}

        if self._simulation:
            total_profit = sum(p.profit for p in self._sim_positions.values())
            return {
                "login": self.config.login or 99999,
                "balance": self._sim_balance,
                "equity": self._sim_balance + total_profit,
                "margin": 0.0,
                "margin_free": self._sim_balance + total_profit,
                "margin_level": 0.0,
                "currency": "USD",
                "server": "Simulation",
            }

        info = self._mt5.account_info()
        if info:
            return {
                "login": info.login,
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "margin_free": info.margin_free,
                "margin_level": info.margin_level,
                "currency": info.currency,
                "server": info.server,
            }
        return {}

    def get_symbol_price(self, symbol: Optional[str] = None) -> Optional[float]:
        """Get current price for symbol"""
        sym = symbol or self.config.symbol
        if not self._connected:
            return None

        if self._simulation:
            return self._sim_price if self._sim_price > 0 else None

        tick = self._mt5.symbol_info_tick(sym)
        if tick:
            return tick.ask  # Use ask for selling (short entry)
        return None

    def set_simulation_price(self, price: float) -> None:
        """Set simulated price (simulation mode only)"""
        if self._simulation:
            self._sim_price = price
            # Update P&L on open positions
            for pos in self._sim_positions.values():
                if pos.type == "SELL":
                    pos.price_current = price
                    pos.profit = (pos.price_open - price) * pos.volume
                elif pos.type == "BUY":
                    pos.price_current = price
                    pos.profit = (price - pos.price_open) * pos.volume

    def open_short(
        self,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "BTC Short Bot",
    ) -> MT5OrderResult:
        """
        Open a BTC short position (SELL).

        Args:
            volume: Position size in lots (e.g. 0.01 = 0.01 BTC)
            stop_loss: Stop loss price (above entry for shorts)
            take_profit: Take profit price (below entry for shorts)
            comment: Order comment

        Returns:
            MT5OrderResult with execution details
        """
        if not self._connected:
            return MT5OrderResult(success=False, message="Not connected")

        symbol = self.config.symbol

        if self._simulation:
            if self._sim_price <= 0:
                return MT5OrderResult(
                    success=False, message="No price set in simulation"
                )

            ticket = self._sim_next_ticket
            self._sim_next_ticket += 1

            position = MT5Position(
                ticket=ticket,
                symbol=symbol,
                volume=volume,
                price_open=self._sim_price,
                price_current=self._sim_price,
                sl=stop_loss or 0.0,
                tp=take_profit or 0.0,
                profit=0.0,
                time=datetime.now(),
                type="SELL",
                magic=self.config.magic_number,
            )
            self._sim_positions[ticket] = position

            logger.info(
                f"SIM: Opened short {volume} {symbol} @ {self._sim_price} "
                f"(SL={stop_loss}, TP={take_profit})"
            )
            return MT5OrderResult(
                success=True,
                order_id=ticket,
                volume=volume,
                price=self._sim_price,
                message="Simulation order filled",
            )

        # Real MT5 order
        price = self._mt5.symbol_info_tick(symbol).bid

        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": self._mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": self.config.deviation,
            "magic": self.config.magic_number,
            "comment": comment,
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self.config.filling_type,
        }

        if stop_loss:
            request["sl"] = stop_loss
        if take_profit:
            request["tp"] = take_profit

        result = self._mt5.order_send(request)

        if result and result.retcode == self._mt5.TRADE_RETCODE_DONE:
            logger.info(
                f"MT5: Opened short {volume} {symbol} @ {result.price} "
                f"(order={result.order})"
            )
            return MT5OrderResult(
                success=True,
                order_id=result.order,
                volume=result.volume,
                price=result.price,
                message="Order filled",
                retcode=result.retcode,
            )

        error_msg = f"Order failed: retcode={result.retcode}" if result else "No result"
        logger.error(f"MT5: {error_msg}")
        return MT5OrderResult(success=False, message=error_msg)

    def close_short(
        self,
        ticket: int,
        volume: Optional[float] = None,
        comment: str = "Close BTC Short",
    ) -> MT5OrderResult:
        """
        Close a short position by buying back.

        Args:
            ticket: Position ticket to close
            volume: Volume to close (None = full position)
            comment: Order comment

        Returns:
            MT5OrderResult
        """
        if not self._connected:
            return MT5OrderResult(success=False, message="Not connected")

        if self._simulation:
            if ticket not in self._sim_positions:
                return MT5OrderResult(
                    success=False, message=f"Position {ticket} not found"
                )

            pos = self._sim_positions[ticket]
            close_volume = volume or pos.volume
            close_price = self._sim_price

            realized_pnl = (pos.price_open - close_price) * close_volume
            self._sim_balance += realized_pnl

            if close_volume >= pos.volume:
                del self._sim_positions[ticket]
            else:
                pos.volume -= close_volume

            logger.info(
                f"SIM: Closed short {close_volume} {pos.symbol} @ {close_price} "
                f"(P&L={realized_pnl:.2f})"
            )
            return MT5OrderResult(
                success=True,
                order_id=ticket,
                volume=close_volume,
                price=close_price,
                message=f"Closed with P&L: {realized_pnl:.2f}",
            )

        # Real MT5 close
        position = None
        positions = self._mt5.positions_get(ticket=ticket)
        if positions:
            position = positions[0]
        else:
            return MT5OrderResult(
                success=False, message=f"Position {ticket} not found"
            )

        close_volume = volume or position.volume
        price = self._mt5.symbol_info_tick(position.symbol).ask

        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": close_volume,
            "type": self._mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": price,
            "deviation": self.config.deviation,
            "magic": self.config.magic_number,
            "comment": comment,
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self.config.filling_type,
        }

        result = self._mt5.order_send(request)

        if result and result.retcode == self._mt5.TRADE_RETCODE_DONE:
            logger.info(f"MT5: Closed short ticket={ticket} @ {result.price}")
            return MT5OrderResult(
                success=True,
                order_id=result.order,
                volume=result.volume,
                price=result.price,
                message="Position closed",
                retcode=result.retcode,
            )

        error_msg = f"Close failed: retcode={result.retcode}" if result else "No result"
        logger.error(f"MT5: {error_msg}")
        return MT5OrderResult(success=False, message=error_msg)

    def get_positions(self, symbol: Optional[str] = None) -> List[MT5Position]:
        """Get open positions, optionally filtered by symbol"""
        if not self._connected:
            return []

        if self._simulation:
            positions = list(self._sim_positions.values())
            if symbol:
                positions = [p for p in positions if p.symbol == symbol]
            return positions

        if symbol:
            mt5_positions = self._mt5.positions_get(symbol=symbol)
        else:
            mt5_positions = self._mt5.positions_get()

        if mt5_positions is None:
            return []

        return [
            MT5Position(
                ticket=p.ticket,
                symbol=p.symbol,
                volume=p.volume,
                price_open=p.price_open,
                price_current=p.price_current,
                sl=p.sl,
                tp=p.tp,
                profit=p.profit,
                time=datetime.fromtimestamp(p.time),
                type="BUY" if p.type == 0 else "SELL",
                magic=p.magic,
            )
            for p in mt5_positions
        ]

    def get_open_short_positions(self) -> List[MT5Position]:
        """Get all open short (SELL) positions for the configured symbol"""
        positions = self.get_positions(symbol=self.config.symbol)
        return [p for p in positions if p.type == "SELL"]

    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> MT5OrderResult:
        """Modify stop loss and/or take profit on an existing position"""
        if not self._connected:
            return MT5OrderResult(success=False, message="Not connected")

        if self._simulation:
            if ticket not in self._sim_positions:
                return MT5OrderResult(
                    success=False, message=f"Position {ticket} not found"
                )
            pos = self._sim_positions[ticket]
            if stop_loss is not None:
                pos.sl = stop_loss
            if take_profit is not None:
                pos.tp = take_profit
            return MT5OrderResult(
                success=True,
                order_id=ticket,
                message="Position modified",
            )

        request = {
            "action": self._mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": self.config.symbol,
        }
        if stop_loss is not None:
            request["sl"] = stop_loss
        if take_profit is not None:
            request["tp"] = take_profit

        result = self._mt5.order_send(request)
        if result and result.retcode == self._mt5.TRADE_RETCODE_DONE:
            return MT5OrderResult(
                success=True, order_id=ticket, message="Position modified"
            )
        error_msg = f"Modify failed: retcode={result.retcode}" if result else "No result"
        return MT5OrderResult(success=False, message=error_msg)
