"""
Strategy Base Module
====================

Responsibility:
    - Define the interface for all strategies.
    - Serve as the API Reference for strategy developers.

Developer Guide:
----------------
When you inherit from this class, you gain access to `self.data_handler`.
The type of data you get depends on whether you request a STOCK or an OPTION CHAIN.

1. Accessing STOCK Data (e.g., "SPY")
   ----------------------------------
   > bar = self.data_handler.get_latest_bar("SPY")
   
   Returns a DataFrame with 1 row.
   Useful for technical indicators (SMA, RSI) or market sentiment.
   
   Keys: ["datetime", "open", "high", "low", "close", "volume"]

2. Accessing OPTION CHAIN Data (e.g., "SPY_OPT")
   ---------------------------------------------
   > chain = self.data_handler.get_latest_bar("SPY_OPT")
   
   Returns a DataFrame with N rows (one per contract).
   You MUST filter this table to find the specific contract you want to trade.
   
   Keys: ["symbol", "expiry", "strike", "option_type", "bid", "ask", "underlying_price"]
   
   Common Recipes:
   ---------------
   a) Get all CALLS expiring next month:
      calls = chain.filter(
          (pl.col("option_type") == "C") & 
          (pl.col("expiry") == desired_date)
      )
      
   b) Find the At-The-Money (ATM) Put:
      # Calculate distance to current underlying price
      puts = chain.filter(pl.col("option_type") == "P")
      puts = puts.with_columns(
          (pl.col("strike") - current_price).abs().alias("dist")
      )
      best_put = puts.sort("dist").head(1)
"""

from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
import polars as pl
from src.events import SignalEvent

class Strategy(ABC):
    def __init__(self, data_handler, portfolio):
        """
        Initializes the strategy with access to the market and the portfolio.
        """
        self.data_handler = data_handler
        self.portfolio = portfolio

    @abstractmethod
    def on_bar(self, current_time: datetime) -> List[SignalEvent]:
        """
        The Main Strategy Loop. Called by the Engine on every time step.

        Parameters:
            current_time (datetime): The specific time of the current bar.

        Returns:
            List[SignalEvent]: A list of actions to take. Return [] if no action.

        Example Implementation (Stock + Options):
        -----------------------------------------
        def on_bar(self, current_time):
            # 1. Get Stock Level Info
            stock_bar = self.data_handler.get_latest_bar("SPY")
            if stock_bar is None: return []
            
            curr_price = stock_bar["close"][0]

            # 2. Get Full Option Chain
            chain = self.data_handler.get_latest_bar("SPY_OPT")
            if chain is None: return []

            # 3. Strategy Logic: If Stock > 400, Buy ATM Call
            if curr_price > 400:
                
                # Filter the chain for Calls
                calls = chain.filter(pl.col("option_type") == "C")
                
                # Find Strike closest to Price (ATM)
                # We use Polars magic to sort by absolute difference
                best_call = calls.sort(
                    (pl.col("strike") - curr_price).abs()
                ).head(1)
                
                if not best_call.is_empty():
                    # Extract symbol from the specific row found
                    sym = best_call["symbol"][0]
                    strike = best_call["strike"][0]
                    
                    return [SignalEvent(
                        symbol=sym, 
                        datetime=current_time, 
                        signal_type="LONG",
                        meta={"strike": strike, "option_type": "C"}
                    )]
            return []
        """
        raise NotImplementedError("Strategies must implement on_bar()")