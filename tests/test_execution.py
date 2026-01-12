import pytest
import polars as pl
from datetime import datetime, date
from src.events import OrderEvent
from src.execution.broker import ExecutionHandler
from src.execution.exchange import OptionExchange
from src.portfolio.portfolio import Portfolio

# --- MOCKS ---

class MockDataHandler:
    def __init__(self):
        self.current_time = datetime(2023, 1, 20, 16, 0, 0) # Expiration Day
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

def test_execution_handler_fills():
    dh = MockDataHandler()
    exec_handler = ExecutionHandler(dh)
    
    # 1. Test Buy Order (Should fill at Ask)
    order = OrderEvent("SPY_CALL", 1, "MARKET", meta={"option_type": "C"})
    fill = exec_handler.execute_order(order)
    
    assert fill.fill_price == 5.2 # Ask Price
    assert fill.commission == 0.65 # Option Comm
    assert fill.quantity == 1

def test_exchange_expiration_logic():
    dh = MockDataHandler()
    exchange = OptionExchange(dh)
    portfolio = Portfolio()
    
    # Setup: We own 1 ITM Call (Strike 400, Underlying 405)
    # And 1 OTM Put (Strike 400, Underlying 405)
    
    # Add ITM Call
    portfolio.add_position("SPY_CALL", 1, 2.0, meta={
        "strike": 400, "expiry": date(2023, 1, 20), "option_type": "C"
    })
    
    # Add OTM Put
    portfolio.add_position("SPY_PUT", 1, 2.0, meta={
        "strike": 400, "expiry": date(2023, 1, 20), "option_type": "P"
    })
    
    # Run Expiration Check
    fills = exchange.check_expiration(portfolio)
    
    # We expect 3 Fills:
    # 1. Close ITM Call (Qty -1)
    # 2. Buy Stock for Call (Qty +100)
    # 3. Close OTM Put (Qty -1)
    
    assert len(fills) == 3
    
    # Verify Stock Exercise
    stock_fill = next(f for f in fills if f.meta["type"] == "EXERCISE_STOCK")
    assert stock_fill.symbol == "SPY"
    assert stock_fill.quantity == 100
    assert stock_fill.fill_price == 400.0 # Strike Price
    
    # Verify OTM Expiration
    put_fill = next(f for f in fills if f.symbol == "SPY_PUT")
    assert put_fill.fill_price == 0.0