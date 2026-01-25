"""
Swissquote API Integration for OMEGA Trading Engine
Handles order execution, portfolio synchronization, and real-time data streaming
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class SwissquoteConfig:
    """Swissquote API Configuration"""
    api_key: str
    api_secret: str
    account_id: str
    base_url: str = "https://api.swissquote.com/api/v1"
    sandbox_mode: bool = False


class SwissquoteClient:
    """Swissquote API Client"""
    
    def __init__(self, config: SwissquoteConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.base_url
        logger.info(f"Swissquote client initialized for account {config.account_id}")
    
    async def connect(self) -> None:
        """Establish connection to Swissquote API"""
        self.session = aiohttp.ClientSession()
        logger.info("Connected to Swissquote API")
    
    async def disconnect(self) -> None:
        """Close connection to Swissquote API"""
        if self.session:
            await self.session.close()
            logger.info("Disconnected from Swissquote API")
    
    async def authenticate(self) -> bool:
        """Authenticate with Swissquote API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.post(
                f"{self.base_url}/auth/login",
                headers=headers,
                json={'account_id': self.config.account_id}
            ) as response:
                if response.status == 200:
                    logger.info("Successfully authenticated with Swissquote")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
            
            async with self.session.get(
                f"{self.base_url}/accounts/{self.config.account_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved account info: {data}")
                    return data
                else:
                    logger.error(f"Failed to get account info: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
            
            async with self.session.get(
                f"{self.base_url}/accounts/{self.config.account_id}/positions",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data)} positions")
                    return data
                else:
                    logger.error(f"Failed to get positions: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def place_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        order_type: str,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Tuple[bool, Dict]:
        """Place an order on Swissquote"""
        try:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
            
            order_data = {
                'symbol': symbol,
                'quantity': quantity,
                'side': side,
                'orderType': order_type,
                'accountId': self.config.account_id
            }
            
            if price:
                order_data['price'] = price
            if stop_price:
                order_data['stopPrice'] = stop_price
            
            async with self.session.post(
                f"{self.base_url}/orders",
                headers=headers,
                json=order_data
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    logger.info(f"Order placed successfully: {data}")
                    return True, data
                else:
                    error = await response.text()
                    logger.error(f"Failed to place order: {response.status} - {error}")
                    return False, {'error': error}
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False, {'error': str(e)}
    
    async def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """Cancel an existing order"""
        try:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
            
            async with self.session.delete(
                f"{self.base_url}/orders/{order_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.info(f"Order {order_id} cancelled successfully")
                    return True, "Order cancelled"
                else:
                    logger.error(f"Failed to cancel order: {response.status}")
                    return False, f"Failed to cancel: {response.status}"
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False, str(e)
    
    async def stream_market_data(self, symbols: List[str]) -> None:
        """Stream real-time market data via WebSocket"""
        try:
            ws_url = f"{self.base_url.replace('https', 'wss')}/stream"
            
            async with self.session.ws_connect(ws_url) as ws:
                # Subscribe to symbols
                for symbol in symbols:
                    await ws.send_json({
                        'action': 'subscribe',
                        'symbol': symbol,
                        'authorization': self.config.api_key
                    })
                
                # Receive updates
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.JSON:
                        data = msg.data
                        logger.debug(f"Market data update: {data}")
                        yield data
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
        except Exception as e:
            logger.error(f"Error streaming market data: {e}")


class OpenWealthClient:
    """OpenWealth API Client for Portfolio Analytics"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openwealth.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("OpenWealth client initialized")
    
    async def connect(self) -> None:
        """Establish connection to OpenWealth API"""
        self.session = aiohttp.ClientSession()
        logger.info("Connected to OpenWealth API")
    
    async def disconnect(self) -> None:
        """Close connection to OpenWealth API"""
        if self.session:
            await self.session.close()
            logger.info("Disconnected from OpenWealth API")
    
    async def get_portfolio_analytics(self, portfolio_id: str) -> Dict:
        """Get portfolio analytics and metrics"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            async with self.session.get(
                f"{self.base_url}/portfolios/{portfolio_id}/analytics",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved portfolio analytics")
                    return data
                else:
                    logger.error(f"Failed to get analytics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
    
    async def get_risk_metrics(self, portfolio_id: str) -> Dict:
        """Get risk metrics (Sharpe, Sortino, VaR, etc.)"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            async with self.session.get(
                f"{self.base_url}/portfolios/{portfolio_id}/risk-metrics",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved risk metrics")
                    return data
                else:
                    logger.error(f"Failed to get risk metrics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {}
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> List[Dict]:
        """Get historical price data"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            params = {
                'symbol': symbol,
                'startDate': start_date,
                'endDate': end_date,
                'interval': interval
            }
            
            async with self.session.get(
                f"{self.base_url}/historical-data",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data)} historical data points for {symbol}")
                    return data
                else:
                    logger.error(f"Failed to get historical data: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []


# Example usage
async def main():
    # Swissquote configuration
    sq_config = SwissquoteConfig(
        api_key="your_api_key",
        api_secret="your_api_secret",
        account_id="your_account_id",
        sandbox_mode=True
    )
    
    # Initialize clients
    sq_client = SwissquoteClient(sq_config)
    ow_client = OpenWealthClient(api_key="your_openwealth_key")
    
    try:
        # Connect
        await sq_client.connect()
        await ow_client.connect()
        
        # Authenticate
        if await sq_client.authenticate():
            # Get account info
            account_info = await sq_client.get_account_info()
            print(f"Account Info: {account_info}")
            
            # Get positions
            positions = await sq_client.get_positions()
            print(f"Positions: {positions}")
            
            # Place an order
            success, order_data = await sq_client.place_order(
                symbol='AAPL',
                quantity=10,
                side='BUY',
                order_type='MARKET'
            )
            
            if success:
                print(f"Order placed: {order_data}")
            
            # Get portfolio analytics
            analytics = await ow_client.get_portfolio_analytics("portfolio_id")
            print(f"Analytics: {analytics}")
    
    finally:
        await sq_client.disconnect()
        await ow_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
