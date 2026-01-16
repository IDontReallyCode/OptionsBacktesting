"""
05_stock_trend_strategy.py

PURPOSE:
    Demonstrates a simple Stock-Only backtest using the Event-Driven Engine.
    
    Strategy: Moving Average Crossover (Fast vs Slow)
    Asset:    Stock (No Options)
    Logic:    Buy when Fast > Slow, Sell when Fast < Slow
    
USAGE:
    $ python examples/05_stock_trend_strategy.py
"""

import os
import sys
import matplotlib.pyplot as plt

# --- PATH SETUP ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- IMPORTS ---
# Corrected based on your actual file structure
from src.data.loader import load_and_standardize, DataSourceConfig
from src.data.handler import DataHandler
from src.portfolio.portfolio import Portfolio
from src.execution.broker import Broker          # Changed from SimulatedBroker
from src.engine import BacktestEngine            # Changed from src.backtest.engine
from src.strategy.stock_basic import MovingAverageCrossStrategy
from src.execution.exchange import OptionExchange      # Even if options do not need to be handled, it is required.   

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

TICKER = "SAMPLE"
INITIAL_CAPITAL = 10000.0

# Define File Paths
STOCK_PATH = os.path.join(project_root, "../data", "SAMPLEdailystock.csv")
PROCESSED_DIR = os.path.join(project_root, "data", "processed")

# Define Data Mapping (Raw CSV -> Standard Columns)
# CRITICAL: We map 'close' -> 'underlying_price' so the Broker finds it!
STOCK_MAP = {
    "date_eod": "datetime",
    "close": "underlying_price", 
    "volume": "volume"
}

# Strategy Parameters
FAST_MA = 50
SLOW_MA = 200

# =============================================================================
# 2. RUN BACKTEST
# =============================================================================

def run_backtest():
    print("=== 05_stock_trend_strategy.py Started ===")

    # ---------------------------------------------------------
    # STEP 1: Load Data (ETL)
    # ---------------------------------------------------------
    print("\n[1] Loading Data...")
    stock_config = DataSourceConfig(name="Stock", col_map=STOCK_MAP)
    
    # This creates/loads 'data/processed/SAMPLE.arrow'
    # Note: If SAMPLE.arrow exists with different columns, delete it first to be safe!
    df_stock, meta = load_and_standardize(TICKER, STOCK_PATH, stock_config, PROCESSED_DIR)
    print(f"    Loaded {len(df_stock)} rows from {meta['source']}")

    # ---------------------------------------------------------
    # STEP 2: Initialize Core Components
    # ---------------------------------------------------------
    print("\n[2] Initializing Backtest Components...")
    
    # A. Data Handler
    # FIX: Create a map with the FULL PATH to the file.
    # The DataHandler only takes one argument: the map.
    file_map = {
        TICKER: os.path.join(PROCESSED_DIR, f"{TICKER}.arrow")
    } 
    
    # Pass ONLY the map. The handler will read the paths directly from it.
    data_handler = DataHandler(file_map)
    
    # B. Portfolio (Tracks Cash & Positions)
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    
    # C. Broker (Executes Orders)
    # We pass the data_handler so the broker can look up prices
    broker = Broker(data_handler)
    
    # NEW: Initialize the Exchange
    # It needs data_handler to check dates and prices for expiration logic
    exchange = OptionExchange(data_handler) 
    
    # D. Strategy
    strategy = MovingAverageCrossStrategy(
        data_handler=data_handler,
        portfolio=portfolio,
        symbol=TICKER,
        fast_window=FAST_MA,
        slow_window=SLOW_MA
    )
    
    # ---------------------------------------------------------
    # STEP 3: The Engine (The Clock)
    # ---------------------------------------------------------
    print(f"\n[3] Running Strategy (MA {FAST_MA} / {SLOW_MA})...")
    
    # FIX: Pass the 'exchange' object here
    engine = BacktestEngine(
        data_handler=data_handler,
        portfolio=portfolio,
        strategy=strategy,
        broker=broker,
        exchange=exchange 
    )

    # Run the simulation loop
    engine.run()
    
    # ---------------------------------------------------------
    # STEP 4: Analysis
    # ---------------------------------------------------------
    print("\n[4] Backtest Finished. Results:")
    final_value = portfolio.get_total_equity()
    pnl = final_value - INITIAL_CAPITAL
    ret = (pnl / INITIAL_CAPITAL) * 100
    
    print(f"    Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"    Final Equity:    ${final_value:,.2f}")
    print(f"    Total Return:    {ret:.2f}%")
    
    # Simple Plot of Equity Curve
    equity_curve = portfolio.history # List of {'datetime': dt, 'equity': float}
    if equity_curve:
        dates = [x['datetime'] for x in equity_curve]
        vals = [x['equity'] for x in equity_curve]
        
        plt.figure(figsize=(10, 6))
        plt.plot(dates, vals, label="Portfolio Equity")
        plt.title(f"Backtest: {TICKER} MA Crossover ({FAST_MA}/{SLOW_MA})")
        plt.xlabel("Date")
        plt.ylabel("Equity ($)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

if __name__ == "__main__":
    run_backtest()
    # try:
    #     run_backtest()
    # except KeyboardInterrupt:
    #     print("\n[Stopped by User]")
    # except Exception as e:
    #     print(f"\n[CRITICAL ERROR] {e}")
    #     import traceback
    #     traceback.print_exc()