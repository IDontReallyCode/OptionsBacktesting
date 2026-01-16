"""
Stock-Only Strategies
=====================
Simple strategies that trade the underlying asset directly.
"""
from typing import List
from datetime import datetime
from src.strategy.base import Strategy
from src.events import SignalEvent

class MovingAverageCrossStrategy(Strategy):
    """
    Classic Moving Average Crossover.
    
    Long Entry: Fast MA > Slow MA
    Exit:       Fast MA < Slow MA
    
    This is an Event-Driven implementation. It does not look ahead.
    It builds the Moving Average iteratively as new bars arrive.
    """
    def __init__(self, data_handler, portfolio, 
                 symbol="SAMPLE", 
                 fast_window=50, 
                 slow_window=200):
        super().__init__(data_handler, portfolio)
        self.symbol = symbol
        self.fast_window = fast_window
        self.slow_window = slow_window
        
        # We keep a history of close prices to calculate MA on the fly
        self.price_history = [] 

    def on_bar(self, current_time: datetime) -> List[SignalEvent]:
        # 1. Get Latest Data
        bar = self.data_handler.get_latest_bar(self.symbol)
        if bar is None or bar.is_empty():
            return []
            
        # Extract Close Price (Assume 'underlying_price' or 'close' exists)
        # The loader standardizes this to 'underlying_price' usually, but check your mapping
        try:
            current_price = bar["underlying_price"][0]
        except:
            current_price = bar["close"][0]
            
        self.price_history.append(current_price)
        
        # 2. Warm-up Period
        # We cannot trade until we have enough data for the Slow MA
        if len(self.price_history) < self.slow_window:
            return []
            
        # 3. Calculate Indicators
        # Slice the list to get the windows
        fast_prices = self.price_history[-self.fast_window:]
        slow_prices = self.price_history[-self.slow_window:]
        
        ma_fast = sum(fast_prices) / len(fast_prices)
        ma_slow = sum(slow_prices) / len(slow_prices)
        
        # 4. Check Current Position
        # In this simple engine, we check if we hold the symbol
        current_holdings = self.portfolio.positions.get(self.symbol, None)
        has_position = current_holdings is not None and current_holdings.quantity > 0
        
        signals = []
        
        # 5. Trading Logic
        
        # ENTRY Signal (Golden Cross)
        # Only buy if we are not already long
        if ma_fast > ma_slow and not has_position:
            print(f"[{current_time}] BUY SIGNAL @ {current_price:.2f} (Fast: {ma_fast:.2f} > Slow: {ma_slow:.2f})")
            signals.append(SignalEvent(
                symbol=self.symbol,
                datetime=current_time,
                signal_type="LONG", # Engine interprets this as "Buy Stock"
                strength=1.0
            ))
            
        # EXIT Signal (Death Cross)
        # Only sell if we actually have something to sell
        elif ma_fast < ma_slow and has_position:
            print(f"[{current_time}] SELL SIGNAL @ {current_price:.2f} (Fast: {ma_fast:.2f} < Slow: {ma_slow:.2f})")
            signals.append(SignalEvent(
                symbol=self.symbol,
                datetime=current_time,
                signal_type="EXIT", # Engine interprets this as "Close Position"
                strength=1.0
            ))
            
        return signals