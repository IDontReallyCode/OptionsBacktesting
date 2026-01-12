"""
Position Module
===============

Responsibility:
    - Track the state of a single asset (Stock or Option).
    - Encapsulate asset-specific logic (e.g., Options have expiries and multipliers).
    - Store Greeks and PnL for that specific trade.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Literal
from datetime import date, datetime

@dataclass
class Position:
    """
    Base class for any financial instrument.
    """
    symbol: str
    quantity: float  # + for Long, - for Short
    avg_price: float # Average entry price
    
    # Current State (Updated every bar)
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    def update_market_value(self, price: float):
        """
        Updates the position's value based on the latest market price.
        """
        self.current_price = price
        self.market_value = price * self.quantity
        self.unrealized_pnl = (price - self.avg_price) * self.quantity

    def close_portion(self, quantity: float, price: float) -> float:
        """
        Reduces the position by `quantity` at `price`. 
        Returns the realized PnL for this specific trade.
        """
        # Note: simplistic FIFO/Weighted avg logic for now
        if abs(quantity) > abs(self.quantity):
            raise ValueError(f"Cannot close {quantity} of {self.symbol}, only have {self.quantity}")
        
        trade_pnl = (price - self.avg_price) * quantity
        self.realized_pnl += trade_pnl
        self.quantity -= quantity
        
        return trade_pnl

@dataclass
class OptionPosition(Position):
    """
    Specialized Logic for Options.
    """
    strike: float = 0.0
    expiry: Optional[date] = None
    option_type: Literal["C", "P"] = "C"
    multiplier: int = 100  # Standard US Equity Option multiplier
    
    # Greeks (Updated by Strategy or Risk Model later)
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

    def update_market_value(self, price: float):
        """
        Override: Options have a multiplier (usually 100).
        Price $1.50 * 100 * 1 contract = $150 Value.
        """
        self.current_price = price
        self.market_value = price * self.quantity * self.multiplier
        self.unrealized_pnl = (price - self.avg_price) * self.quantity * self.multiplier

    def is_itm(self, underlying_price: float) -> bool:
        """
        Checks if the option is In-The-Money.
        """
        if self.option_type == "C":
            return underlying_price > self.strike
        else:
            return underlying_price < self.strike

    def days_to_expiry(self, current_date: datetime) -> int:
        if not self.expiry:
            return 0
        # Ensure we are comparing dates, not datetimes
        delta = self.expiry - current_date.date()
        return max(0, delta.days)