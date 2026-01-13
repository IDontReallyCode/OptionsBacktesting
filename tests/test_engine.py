import pytest
import polars as pl
from datetime import datetime
from src.engine import BacktestEngine
from src.portfolio.portfolio import Portfolio
from src.execution.broker import Broker
from src.execution.exchange import OptionExchange
from src.strategy.base import Strategy
from src.events import SignalEvent

# --- MOCKS ---

class MockDataHandler:
    def __init__(self):
        self.continue_backtest = True
        self.times = [datetime(2023, 1, 1, 10, 0), datetime(2023, 1, 1, 10, 1)]
        self.idx = 0
        
        # Simple Data
        self.data = {
            "SPY": pl.DataFrame({"underlying_price": [100.0]}),
            "SPY_OPT": pl.DataFrame({"bid": [5.0], "ask": [5.2]})
        }

    def update_bars(self):
        if self.idx >= len(self.times):
            self.continue_backtest = False
            return False
        self.idx += 1
        return True
        
    def get_current_time(self):
        return self.times[self.idx - 1]

    def get_latest_bar(self, symbol):
        return self.data.get(symbol)

# Inside MockStrategy class in tests/test_engine.py
class MockStrategy(Strategy):
    """Fires a BUY signal on the first bar only."""
    def on_bar(self, current_time):
        if current_time.minute == 0: # First bar
            # FIXED: Added "strike": 100 to meta
            return [SignalEvent(
                "SPY_OPT", 
                current_time, 
                "LONG", 
                meta={"option_type": "C", "strike": 100} 
            )]
        return []
    
    
# --- TEST ---

def test_engine_end_to_end():
    # 1. Setup Components
    dh = MockDataHandler()
    port = Portfolio(initial_capital=10000.0)
    strat = MockStrategy(dh, port)
    broker = Broker(dh)
    exchange = OptionExchange(dh)
    
    # 2. Init Engine
    engine = BacktestEngine(dh, port, strat, broker, exchange)
    
    # 3. Run
    engine.run()
    
    # 4. Verify Results
    
    # We should have 2 history points
    assert len(engine.history) == 2
    
    # Check Position: Should have bought 1 contract
    pos = port.get_position("SPY_OPT")
    assert pos is not None
    assert pos.quantity == 1
    
    # Check Cash: 
    # Start 10,000
    # Bought 1 contract @ Ask 5.2 (Multiplier 100) = $520
    # Commission $0.65
    # Remaining Cash = 9479.35
    assert port.current_cash == 9479.35