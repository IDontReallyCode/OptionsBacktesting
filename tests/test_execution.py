import pytest
import polars as pl
from datetime import datetime, date
from src.events import OrderEvent
from src.execution.broker import Broker
from src.execution.exchange import OptionExchange
from src.portfolio.portfolio import Portfolio

# --- MOCKS ---

class MockDataHandler:
    def __init__(self):
        self.current_time = datetime(2023, 1, 20, 16, 0, 0)
        self.data = {
            "SPY": pl.DataFrame({
                "underlying_price": [405.0], "bid": [404.9], "ask": [405.1]
            }),
            "SPY_CALL": pl.DataFrame({
                "bid": [5.0], "ask": [5.2], "mid": [5.1]
            })
        }
    
    def get_latest_bar(self, symbol):
        return self.data.get(symbol)
        
    def get_current_time(self):
        return self.current_time

# --- TESTS ---

def test_broker_fills():
    dh = MockDataHandler()
    # Now using the renamed Broker class
    broker = Broker(dh)
    
    # 1. Test Buy Order (Should fill at Ask)
    order = OrderEvent("SPY_CALL", 1, "MARKET", meta={"option_type": "C"})
    fill = broker.execute_order(order)
    
    assert fill.fill_price == 5.2 # Ask Price
    assert fill.commission == 0.65 # Option Comm
    assert fill.quantity == 1

def test_exchange_expiration_logic():
    dh = MockDataHandler()
    exchange = OptionExchange(dh)
    portfolio = Portfolio()
    
    # Setup: ITM Call (Strike 400, Underlying 405)
    portfolio.add_position("SPY_CALL", 1, 2.0, meta={
        "strike": 400, "expiry": date(2023, 1, 20), "option_type": "C"
    })
    
    # Setup: OTM Put (Strike 400, Underlying 405)
    portfolio.add_position("SPY_PUT", 1, 2.0, meta={
        "strike": 400, "expiry": date(2023, 1, 20), "option_type": "P"
    })
    
    # Run Expiration
    fills = exchange.check_expiration(portfolio)
    
    assert len(fills) == 3
    # Verify Stock Exercise
    stock_fill = next(f for f in fills if f.meta["type"] == "EXERCISE_STOCK")
    assert stock_fill.symbol == "SPY"
    assert stock_fill.quantity == 100
    assert stock_fill.fill_price == 400.0