import pytest
import polars as pl
from datetime import datetime, date
from src.strategy.example_MA_buy_call import SmaOptionStrategy
from src.portfolio.portfolio import Portfolio

class MockDataHandler:
    def __init__(self, prices, chain_data):
        self.prices = prices
        self.chain_data = chain_data
        self.idx = 0
        self.time = datetime(2023, 1, 1, 9, 30)

    def get_latest_bar(self, symbol):
        if self.idx >= len(self.prices): return None
        
        if symbol == "SPY":
            return pl.DataFrame({"underlying_price": [float(self.prices[self.idx])]})
        elif symbol == "SPY_OPT":
            return self.chain_data
        return None
    
    def step(self):
        self.idx += 1

def test_strategy_contract_selection():
    # 1. Prices: Flat then Jump (Trigger Bull Signal)
    prices = [400] * 20 + [410]
    
    # 2. Mock Option Chain (2 contracts)
    # Contract A: Expires in 30 days, Strike 410 (Perfect ATM)
    # Contract B: Expires in 30 days, Strike 450 (Deep OTM)
    chain_df = pl.DataFrame({
        "symbol": ["SPY_OPT_A", "SPY_OPT_B"],
        "option_type": ["C", "C"],
        "expiry": [datetime(2023, 1, 31), datetime(2023, 1, 31)], # ~30 days from Jan 1
        "strike": [410.0, 450.0],
        "bid": [5.0, 0.5],
        "ask": [5.1, 0.6]
    })
    
    dh = MockDataHandler(prices, chain_df)
    port = Portfolio()
    
    strategy = SmaOptionStrategy(dh, port, target_dte=30)
    
    # Run warmup
    for _ in range(20):
        strategy.on_bar(dh.time)
        dh.step()
        
    # Trigger Signal
    signals = strategy.on_bar(dh.time)
    
    assert len(signals) == 1
    # Should select Contract A (Strike 410 is closer to Price 410 than 450)
    assert signals[0].symbol == "SPY_OPT_A"
    assert signals[0].meta["strike"] == 410.0