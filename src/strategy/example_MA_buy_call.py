"""
Example Strategies
==================
"""
import polars as pl
from typing import List, Optional
from datetime import datetime, timedelta
from src.strategy.base import Strategy
from src.events import SignalEvent

class SmaOptionStrategy(Strategy):
    def __init__(self, data_handler, portfolio, 
                 underlying_symbol="SPY", 
                 chain_symbol="SPY_OPT", 
                 sma_window=20,
                 target_dte=30):
        super().__init__(data_handler, portfolio)
        self.u_symbol = underlying_symbol
        self.chain_symbol = chain_symbol # The key for the full option chain data
        self.window = sma_window
        self.target_dte = target_dte
        
        self.price_history = [] 

    def on_bar(self, current_time: datetime) -> List[SignalEvent]:
        # 1. Get Underlying Data
        u_data = self.data_handler.get_latest_bar(self.u_symbol)
        if u_data is None or u_data.is_empty():
            return []
            
        current_price = u_data["underlying_price"][0]
        self.price_history.append(current_price)
        
        if len(self.price_history) > self.window:
            self.price_history.pop(0)
            
        if len(self.price_history) < self.window:
            return []
            
        sma = sum(self.price_history) / self.window
        
        # 2. Check Existing Position (Simplify: Do we own ANY option on this underlying?)
        # In a real engine, we'd check specifically for the contract we hold.
        has_position = False
        for sym in self.portfolio.positions:
            if sym.startswith(self.u_symbol) and sym != self.u_symbol:
                has_position = True
                break
        
        signals = []
        
        # 3. ENTRY LOGIC: Price > SMA -> Buy Call
        if current_price > sma and not has_position:
            
            # --- CONTRACT SELECTION LOGIC ---
            # Get the full option chain for this minute
            chain_df = self.data_handler.get_latest_bar(self.chain_symbol)
            
            if chain_df is not None and not chain_df.is_empty():
                selected = self._select_option_contract(
                    chain_df, current_price, current_time, option_type="C"
                )
                
                if selected:
                    print(f"[{current_time}] Bullish Signal. Selected: {selected['symbol']}")
                    signals.append(SignalEvent(
                        symbol=selected['symbol'],
                        datetime=current_time,
                        signal_type="LONG",
                        strength=1.0,
                        meta={
                            "strike": selected['strike'],
                            "expiry": selected['expiry'],
                            "option_type": "C"
                        }
                    ))

        # 4. EXIT LOGIC: Price < SMA -> Close All
        elif current_price < sma and has_position:
            print(f"[{current_time}] Bearish Signal. Closing all positions.")
            # Find all option positions and close them
            for sym in self.portfolio.positions:
                if sym.startswith(self.u_symbol) and sym != self.u_symbol:
                    signals.append(SignalEvent(
                        symbol=sym,
                        datetime=current_time,
                        signal_type="EXIT",
                        strength=1.0
                    ))
            
        return signals

    def _select_option_contract(self, chain_df: pl.DataFrame, 
                                underlying_price: float, 
                                current_time: datetime,
                                option_type: str) -> Optional[dict]:
        """
        Filters the chain to find the 'Best' contract.
        Criteria:
        1. Right Type (Call/Put)
        2. DTE closest to self.target_dte (e.g. 30 days)
        3. Strike closest to underlying_price (ATM)
        """
        # 1. Filter by Option Type
        # Note: We cast to string to be safe if it's Categorical
        filtered = chain_df.filter(
            pl.col("option_type").cast(pl.Utf8) == option_type
        )
        
        if filtered.is_empty():
            return None

        # 2. Calculate DTE (Days to Expiration)
        # We assume 'expiry' column exists and is Date/Datetime
        # We add a 'dte' column temporarily
        filtered = filtered.with_columns(
            (pl.col("expiry") - current_time).dt.total_days().alias("dte")
        )
        
        # Filter for reasonable DTE (e.g., +/- 10 days from target)
        # filtered = filtered.filter(
        #     (pl.col("dte") - self.target_dte).abs() < 10
        # )

        # 3. Sort to find the "Best" match
        # Primary Sort: DTE closest to target
        # Secondary Sort: Strike closest to Underlying (ATM)
        
        # We calculate 'abs_diff_strike' and 'abs_diff_dte'
        filtered = filtered.with_columns([
            (pl.col("strike") - underlying_price).abs().alias("dist_strike"),
            (pl.col("dte") - self.target_dte).abs().alias("dist_dte")
        ])
        
        # Sort by DTE distance first, then Strike distance
        sorted_df = filtered.sort(["dist_dte", "dist_strike"])
        
        if sorted_df.is_empty():
            return None
            
        # Return the top row as a dictionary
        best_row = sorted_df.row(0, named=True)
        return best_row