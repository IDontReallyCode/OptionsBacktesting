"""
Events Module
=============
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Event:
    pass

@dataclass
class MarketEvent(Event):
    time: datetime

@dataclass
class SignalEvent(Event):
    symbol: str
    datetime: datetime
    signal_type: str       # "LONG" or "SHORT" (or "EXIT")
    strength: float = 1.0 
    meta: Optional[Dict[str, Any]] = None # <--- ADDED THIS

@dataclass
class OrderEvent(Event):
    symbol: str
    quantity: float
    order_type: str = "MARKET"
    price: Optional[float] = None 
    meta: Optional[Dict[str, Any]] = None

@dataclass
class FillEvent(Event):
    datetime: datetime
    symbol: str
    quantity: float
    fill_price: float
    commission: float
    exchange: str = "SIMULATED"
    meta: Optional[Dict[str, Any]] = None