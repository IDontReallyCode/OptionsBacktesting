"""
Broker Module
=============

Responsibility:
    - Simulate the Execution of orders.
    - Model Slippage (Bid/Ask spread).
    - Calculate Commissions.
"""

from src.events import OrderEvent, FillEvent
from typing import Optional

class Broker:
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def execute_order(self, order: OrderEvent) -> Optional[FillEvent]:
        """
        Converts an Order into a Fill based on current market data.
        """
        # 1. Get Live Price
        price_slice = self.data_handler.get_latest_bar(order.symbol)
        
        if price_slice is None or price_slice.is_empty():
            print(f"[Broker] No data for {order.symbol}. Order Ignored.")
            return None

        # 2. Calculate Fill Price (Simulation Logic)
        fill_price = self._calculate_fill_price(price_slice, order.quantity)
        
        # 3. Calculate Commission (e.g., $0.65 per contract)
        commission = self._calculate_commission(order.quantity, order.meta)

        # 4. Create Fill
        return FillEvent(
            datetime=self.data_handler.get_current_time(),
            symbol=order.symbol,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
            meta=order.meta
        )

    def _calculate_fill_price(self, df, quantity: float) -> float:
        """
        Determines the price. 
        Pessimistic: Buy at Ask, Sell at Bid.
        """
        cols = df.columns
        if "bid" in cols and "ask" in cols:
            bid = df["bid"][0]
            ask = df["ask"][0]
            if quantity > 0:
                return ask  # Buying? Pay the Ask.
            else:
                return bid  # Selling? Take the Bid.
                
        # Fallback
        if "mid" in cols: return df["mid"][0]
        if "underlying_price" in cols: return df["underlying_price"][0]
        
        return 0.0

    def _calculate_commission(self, quantity: float, meta: dict) -> float:
        """
        Simple model: $0.00 for stock, $0.65 for options.
        """
        if meta and "option_type" in meta:
            return abs(quantity) * 0.65
        return 0.0