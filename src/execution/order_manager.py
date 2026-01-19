"""Order management systems"""

from typing import Dict, List, Optional


class OrderManager:
    """Manage orders and order lifecycle"""
    
    def __init__(self):
        self.active_orders = {}
        self.filled_orders = []
        self.order_counter = 0
    
    def create_order(self, symbol: str, quantity: float, side: str = "BUY") -> str:
        """Create new order"""
        order_id = f"ORD_{self.order_counter}"
        self.order_counter += 1
        
        self.active_orders[order_id] = {
            'id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'side': side,
            'status': 'PENDING'
        }
        return order_id
    
    def fill_order(self, order_id: str, filled_qty: float, filled_price: float):
        """Fill an order"""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order['filled_quantity'] = filled_qty
            order['filled_price'] = filled_price
            order['status'] = 'FILLED'
            self.filled_orders.append(order)
            del self.active_orders[order_id]
    
    def cancel_order(self, order_id: str):
        """Cancel an order"""
        if order_id in self.active_orders:
            self.active_orders[order_id]['status'] = 'CANCELLED'
            del self.active_orders[order_id]
