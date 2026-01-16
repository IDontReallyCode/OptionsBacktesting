"""
Option Exchange Module
======================

Responsibility:
    - Monitor option lifecycles.
    - Auto-Exercise ITM options at expiration.
    - Expire OTM options worthless.
"""

from src.events import FillEvent
from typing import List
from datetime import datetime, date

class OptionExchange:
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def check_expiration(self, portfolio) -> List[FillEvent]:
        """
        Scans the portfolio for options that expire TODAY.
        """
        current_dt = self.data_handler.get_current_time()
        if not current_dt:
            return []
            
        # --- FIX START ---
        # If it's a full datetime (YYYY-MM-DD HH:MM:SS), strip the time.
        # If it's already a date (YYYY-MM-DD), use it as is.
        if isinstance(current_dt, datetime):
            current_date = current_dt.date()
        else:
            current_date = current_dt
        # --- FIX END ---
        generated_fills = []

        for symbol, position in portfolio.positions.items():
            
            # 1. Skip if not an Option or not Expiring Today
            if not hasattr(position, "expiry") or position.expiry is None:
                continue
                
            if current_date >= position.expiry:
                
                # 2. Determine Settlement Price
                # Hack: Assume underlying symbol is the first part "SPY" of "SPY_OPT"
                underlying_sym = symbol.split("_")[0] 
                price_slice = self.data_handler.get_latest_bar(underlying_sym)
                
                if price_slice is None or price_slice.is_empty():
                    print(f"[Exchange] Cannot settle {symbol}: No data for {underlying_sym}")
                    continue
                    
                settlement_price = price_slice["underlying_price"][0]
                
                # 3. Check Moneyness
                if position.is_itm(settlement_price):
                    print(f"[Exchange] Exercising ITM Option: {symbol}")
                    generated_fills.extend(
                        self._exercise_position(position, settlement_price, current_dt)
                    )
                else:
                    print(f"[Exchange] Expiring OTM Option: {symbol}")
                    generated_fills.extend(
                        self._expire_position(position, current_dt)
                    )
                    
        return generated_fills

    def _expire_position(self, position, dt) -> List[FillEvent]:
        """Option expires worthless -> Sell @ 0.0"""
        return [FillEvent(
            datetime=dt,
            symbol=position.symbol,
            quantity=-position.quantity,
            fill_price=0.0,
            commission=0.0,
            meta={"type": "EXPIRATION"}
        )]

    def _exercise_position(self, position, settlement_price, dt) -> List[FillEvent]:
        """Option Exercised -> Close Option, Open Stock."""
        # 1. Close the Option
        close_opt = FillEvent(
            datetime=dt,
            symbol=position.symbol,
            quantity=-position.quantity,
            fill_price=0.0,
            commission=0.0,
            meta={"type": "EXERCISE_CLOSE"}
        )
        
        # 2. Exchange Stocks
        stock_qty = position.quantity * position.multiplier
        if position.option_type == "P":
            stock_qty = -stock_qty
            
        open_stock = FillEvent(
            datetime=dt,
            symbol=position.symbol.split("_")[0],
            quantity=stock_qty,
            fill_price=position.strike,
            commission=0.0,
            meta={"type": "EXERCISE_STOCK"}
        )
        
        return [close_opt, open_stock]