"""
Backtest Engine Module
======================

Responsibility:
    - The "Event Loop": Orchestrates the flow of time.
    - Connects Data -> Portfolio -> Strategy -> Execution.
    - Handling the lifecycle of a single simulation run.
"""

from typing import List
from src.events import SignalEvent, OrderEvent, FillEvent

class BacktestEngine:
    def __init__(self, data_handler, portfolio, strategy, broker, exchange):
        """
        Args:
            data_handler: Source of market data ticks.
            portfolio:    Tracks assets and cash.
            strategy:     Logic for generating signals.
            broker:       Execution handler (fills orders).
            exchange:     Option lifecycle handler (expirations).
        """
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.broker = broker
        self.exchange = exchange
        
        # Performance Tracking
        self.history = [] # To store equity curve, etc.

    def run(self):
        """
        Main Event Loop.
        Steps through time until DataHandler runs out of data.
        """
        print("Starting Backtest...")
        
        while self.data_handler.continue_backtest:
            # 1. Tick: Advance Time
            has_new_data = self.data_handler.update_bars()
            if not has_new_data:
                break
                
            current_time = self.data_handler.get_current_time()
            
            # 2. Exchange Operations (Auto-Exercise/Expire)
            # This happens BEFORE trading (e.g., options expire at open or close)
            expiration_fills = self.exchange.check_expiration(self.portfolio)
            for fill in expiration_fills:
                self._handle_fill(fill)

            # 3. Mark to Market
            # Update the value of everything we currently own
            self.portfolio.mark_to_market(current_time, self.data_handler)
            
            # Record History (Equity Curve)
            self.history.append({
                "time": current_time,
                "equity": self.portfolio.equity,
                "cash": self.portfolio.current_cash
            })

            # 4. Strategy Signal Generation
            signals = self.strategy.on_bar(current_time)
            
            # 5. Signal Processing & Execution
            for signal in signals:
                # Convert Signal -> Order (Basic Risk Management)
                order = self._generate_order(signal)
                
                if order:
                    # Send to Broker -> Get Fill
                    fill = self.broker.execute_order(order)
                    if fill:
                        self._handle_fill(fill)

        print("Backtest Completed.")

    def _generate_order(self, signal: SignalEvent) -> OrderEvent:
        """
        Converts a raw Strategy Signal into a sized Execution Order.
        (In a full system, a RiskManager class would handle this).
        """
        quantity = 0
        
        # Simple Logic: Always trade 1 unit (100 shares or 1 contract)
        if signal.signal_type == "LONG":
            quantity = 1
        elif signal.signal_type == "SHORT":
            quantity = -1
        elif signal.signal_type == "EXIT":
            # Flatten specific position
            pos = self.portfolio.get_position(signal.symbol)
            if pos:
                quantity = -pos.quantity
            else:
                return None
        
        if quantity == 0:
            return None
            
        return OrderEvent(
            symbol=signal.symbol,
            quantity=quantity,
            order_type="MARKET",
            meta=signal.meta
        )

    # Inside src/engine.py, find the _handle_fill method:
    def _handle_fill(self, fill: FillEvent):
        """
        Updates the Portfolio based on a confirmed Trade.
        """
        print(f"[{fill.datetime}] FILL: {fill.symbol} {fill.quantity} @ {fill.fill_price}")
        
        self.portfolio.add_position(
            symbol=fill.symbol,
            quantity=fill.quantity,
            price=fill.fill_price,
            commission=fill.commission,  # <--- FIXED: Pass commission
            meta=fill.meta
        )