"""
Portfolio Module
================

Responsibility:
    - Aggregate all atomic Positions.
    - Track Total Equity and Cash.
    - Mark-to-Market: Update all values based on current DataHandler state.
"""

from typing import Dict, List, Optional
import polars as pl
from .position import Position, OptionPosition

class Portfolio:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.equity = initial_capital
        
        # Store positions by a unique key (usually Symbol)
        # For options, symbol usually includes strike/exp (e.g., "SPY230120C400")
        self.positions: Dict[str, Position] = {}

    def add_cash(self, amount: float):
        self.current_cash += amount

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)

    def mark_to_market(self, current_time, data_handler):
        """
        Updates the value of all positions based on the latest data.
        """
        self.equity = self.current_cash
        
        for symbol, pos in self.positions.items():
            # 1. Fetch latest bar from Handler
            # The handler returns a DataFrame slice for the current time
            df = data_handler.get_latest_bar(symbol)
            
            price = 0.0
            
            # 2. Extract Price safely
            if df is not None and not df.is_empty():
                # We prioritize 'mid', then 'close' (underlying), then 'last'
                if "mid" in df.columns:
                    price = df["mid"][0]
                elif "underlying_price" in df.columns: # Fallback for pure stock feeds
                    price = df["underlying_price"][0]
                elif "bid" in df.columns and "ask" in df.columns:
                    price = (df["bid"][0] + df["ask"][0]) / 2.0
            else:
                # If no data found for this second (illiquid), keep last known price
                price = pos.current_price 

            # 3. Update Position State
            pos.update_market_value(price)
            
            # 4. Add to Total Equity
            self.equity += pos.market_value

    def add_position(self, symbol: str, quantity: float, price: float, 
                     meta: Dict = None):
        """
        Adds a new trade. Handles creation of OptionPosition if meta provided.
        """
        if symbol in self.positions:
            # Average down / Increase size
            existing = self.positions[symbol]
            total_cost = (existing.avg_price * existing.quantity) + (price * quantity)
            existing.quantity += quantity
            existing.avg_price = total_cost / existing.quantity if existing.quantity != 0 else 0.0
        else:
            # Create New
            if meta and "strike" in meta:
                # It's an Option
                self.positions[symbol] = OptionPosition(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=price,
                    strike=meta.get("strike"),
                    expiry=meta.get("expiry"),
                    option_type=meta.get("option_type", "C"),
                    multiplier=100
                )
            else:
                # It's a Stock
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=price
                )
        
        # Deduct Cost from Cash (assuming Long)
        # Note: ExecutionHandler usually calculates precise cost (commissions etc)
        # This is a basic update.
        cost = price * quantity
        if isinstance(self.positions[symbol], OptionPosition):
            cost *= 100
            
        self.current_cash -= cost