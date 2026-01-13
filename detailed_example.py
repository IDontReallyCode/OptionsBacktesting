import os
import polars as pl
import matplotlib.pyplot as plt
from datetime import datetime
import shutil

# --- FRAMEWORK IMPORTS ---
# Ensure your package is installed or in the PYTHONPATH
from src.data.loader import load_and_standardize
from src.data.handler import DataHandler
from src.portfolio.portfolio import Portfolio
from src.execution.broker import Broker
from src.execution.exchange import OptionExchange
from src.engine import BacktestEngine
from src.strategy.base import Strategy
from src.events import SignalEvent

# =============================================================================
# 1. CONFIGURATION & HYPERPARAMETERS
# =============================================================================
CONFIG = {
    # --- File Paths ---
    "RAW_STOCK_PATH": "data/SAMPLEdailystock.csv",
    "RAW_OPTION_PATH": "data/SAMPLEdailyoption.csv",
    "PROCESSED_DIR": "data/processed",
    
    # --- Strategy Parameters ---
    "TICKER": "SAMPLE",
    "FAST_MA": 50,             # Fast Moving Average Window
    "SLOW_MA": 200,            # Slow Moving Average Window
    "OPTION_DTE": 30,          # Target Days to Expiration (NDTE)
    "OPTION_DELTA": 0.50,      # Target Delta (Approximate using Strike vs Price)
    "CLOSE_ON_SIGNAL": True,   # If True, close existing position when signal flips. If False, hold to expiry.
    
    # --- Execution & Portfolio ---
    "INITIAL_CAPITAL": 100_000.0,
    "COMMISSION_PER_CONTRACT": 0.65,
    "EXECUTION_MODE": "WCS",   # "WCS" (Worst Case: Buy Ask/Sell Bid), "BCS" (Best Case), "MID"
    "CHECK_VOLUME": True,      # If True, only trade if option volume > 0
}

# =============================================================================
# 2. DATA PREPARATION & VISUALIZATION
# =============================================================================


def prepare_data():
    """Converts CSVs to Arrow files for the engine."""
    # Ensure import is available for the config object
    from src.data.loader import DataSourceConfig

    if not os.path.exists(CONFIG["PROCESSED_DIR"]):
        os.makedirs(CONFIG["PROCESSED_DIR"])

    print("--- Step 1: Loading & Standardizing Data ---")
    
    # ---------------------------------------------------------
    # 1. Standardize Stock Data
    # ---------------------------------------------------------
    stock_config = {
        # CSV Header -> Internal Standard
        "date_eod": "datetime", 
        "open": "open", 
        "high": "high", 
        "low": "low", 
        "close": "close", 
        "volume": "volume"
    }

    load_and_standardize(
        CONFIG["TICKER"], 
        CONFIG["RAW_STOCK_PATH"], 
        stock_config,
        output_dir=CONFIG["PROCESSED_DIR"]
    )

    # ---------------------------------------------------------
    # 2. Standardize Option Data
    # ---------------------------------------------------------
    # We use DataSourceConfig here because we need a 'val_map' 
    # to translate pcflag (1/0) into C/P.
    opt_conf_obj = DataSourceConfig(
        name="CustomOption",
        col_map={
            "date_eod": "datetime",
            "ticker": "symbol",
            "k": "strike",
            "date_mat": "expiry",
            "bid": "bid",
            "ask": "ask",
            "volume": "volume",
            "pcflag": "option_type" # Maps 'pcflag' to 'option_type'
        },
        val_map={
            "option_type": {1: "C", 0: "P"} # IMPORTANT: 1=Call, 0=Put (adjust if needed)
        }
    )

    load_and_standardize(
        f"{CONFIG['TICKER']}_OPT", 
        CONFIG["RAW_OPTION_PATH"], 
        opt_conf_obj,
        output_dir=CONFIG["PROCESSED_DIR"]
    )
    print("Data processing complete.\n")


def plot_market_analysis(df_stock):
    """Plots Price, Volume, and Moving Averages."""
    print("--- Step 2: Plotting Market Analysis ---")
    
    # Calculate MAs using Polars
    df = df_stock.sort("datetime")
    df = df.with_columns([
        pl.col("close").rolling_mean(CONFIG["FAST_MA"]).alias("fast_ma"),
        pl.col("close").rolling_mean(CONFIG["SLOW_MA"]).alias("slow_ma")
    ])
    
    # Convert to Pandas for easy plotting with Matplotlib
    pdf = df.to_pandas()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot Price & MAs
    ax1.plot(pdf['datetime'], pdf['close'], label='Close Price', color='black', alpha=0.6)
    ax1.plot(pdf['datetime'], pdf['fast_ma'], label=f'{CONFIG["FAST_MA"]} MA', color='blue')
    ax1.plot(pdf['datetime'], pdf['slow_ma'], label=f'{CONFIG["SLOW_MA"]} MA', color='red')
    ax1.set_title(f"{CONFIG['TICKER']} Trend Analysis")
    ax1.set_ylabel("Price")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot Volume
    ax2.bar(pdf['datetime'], pdf['volume'], color='gray', alpha=0.5, label='Volume')
    ax2.set_ylabel("Volume")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    print("Plot displayed.\n")

# =============================================================================
# 3. STRATEGY IMPLEMENTATION
# =============================================================================

class MovingAverageOptionStrategy(Strategy):
    def __init__(self, data_handler, portfolio):
        super().__init__(data_handler, portfolio)
        self.ticker = CONFIG["TICKER"]
        self.opt_ticker = f"{CONFIG['TICKER']}_OPT"
        
        # We keep a small history to calculate MA on the fly (or use pre-calc logic)
        # For efficiency in event-loops, we often calculate MAs incrementally
        self.prices = [] 
        self.dates = []

    def on_bar(self, current_time: datetime):
        # 1. Get Stock Data
        stock_bar = self.data_handler.get_latest_bar(self.ticker)
        if stock_bar is None or stock_bar.is_empty():
            return []
            
        price = stock_bar["close"][0]
        self.prices.append(price)
        
        # Need enough data for Slow MA
        if len(self.prices) < CONFIG["SLOW_MA"]:
            return []
            
        # 2. Calculate MAs
        # Slice the last N items
        fast_series = self.prices[-CONFIG["FAST_MA"]:]
        slow_series = self.prices[-CONFIG["SLOW_MA"]:]
        
        fast_ma = sum(fast_series) / len(fast_series)
        slow_ma = sum(slow_series) / len(slow_series)
        
        # 3. Determine Market State
        # Simple Crossover logic
        # Ideally, check if crossover JUST happened (Fast crossed above Slow)
        # Here we use state-based logic (Bullish vs Bearish zone)
        is_bullish = fast_ma > slow_ma
        is_bearish = fast_ma < slow_ma
        
        signals = []
        
        # Check current holdings
        # We identify our positions by symbol prefix
        current_positions = [
            p for sym, p in self.portfolio.positions.items() 
            if sym.startswith(self.ticker) and sym != self.ticker
        ]
        has_position = len(current_positions) > 0
        
        # --- ENTRY LOGIC ---
        if not has_position:
            if is_bullish:
                # BUY CALL
                contract = self._find_contract(price, current_time, "C")
                if contract:
                    signals.append(self._create_signal(contract, "LONG", current_time))
                    
            elif is_bearish:
                # BUY PUT (Strategy says "buy puts on sell signals", no short selling options)
                contract = self._find_contract(price, current_time, "P")
                if contract:
                    signals.append(self._create_signal(contract, "LONG", current_time))

        # --- EXIT LOGIC (Optional) ---
        elif has_position and CONFIG["CLOSE_ON_SIGNAL"]:
            # If we hold a Call but market turned Bearish -> Close
            # If we hold a Put but market turned Bullish -> Close
            for pos in current_positions:
                is_call = pos.option_type == "C"
                should_close = (is_call and is_bearish) or (not is_call and is_bullish)
                
                if should_close:
                    signals.append(SignalEvent(
                        symbol=pos.symbol,
                        datetime=current_time,
                        signal_type="EXIT"
                    ))
                    # If we close, we might want to immediately reverse. 
                    # For simplicity, we wait for next bar to re-enter.
                    
        return signals

    def _find_contract(self, underlying_price, current_time, opt_type):
        """Scans the option chain for the best fit (DTE & Delta/ATM)."""
        chain = self.data_handler.get_latest_bar(self.opt_ticker)
        if chain is None or chain.is_empty():
            return None
            
        # 1. Filter by Type
        # Note: Ensure your CSV has 'option_type' column ('C' or 'P')
        candidates = chain.filter(pl.col("option_type") == opt_type)
        
        # 2. Check Volume (Optional Feature)
        if CONFIG["CHECK_VOLUME"] and "volume" in candidates.columns:
             candidates = candidates.filter(pl.col("volume") > 0)
        
        if candidates.is_empty():
            return None
            
        # 3. Filter by DTE (Target: CONFIG['OPTION_DTE'])
        # Creates a temp 'days_to_expiry' column
        candidates = candidates.with_columns(
            (pl.col("expiry") - current_time).dt.total_days().alias("dte")
        )
        # Filter reasonably close (e.g. +/- 5 days)
        candidates = candidates.filter(
            (pl.col("dte") - CONFIG["OPTION_DTE"]).abs() < 10
        )
        
        if candidates.is_empty():
            return None
            
        # 4. Filter by Strike (Target: ATM to approximate 0.50 Delta)
        # 0.50 Delta is roughly At-The-Money for close expirations
        candidates = candidates.with_columns(
            (pl.col("strike") - underlying_price).abs().alias("dist_atm")
        )
        
        # Sort by distance to ATM, pick closest
        best_contract = candidates.sort("dist_atm").head(1)
        
        if best_contract.is_empty():
            return None
            
        return best_contract.row(0, named=True)

    def _create_signal(self, contract_row, signal_type, current_time):
        return SignalEvent(
            symbol=contract_row['symbol'],
            datetime=current_time,
            signal_type=signal_type,
            meta={
                "strike": contract_row['strike'],
                "expiry": contract_row['expiry'],
                "option_type": contract_row['option_type']
            }
        )

# =============================================================================
# 4. EXECUTION & RESULTS
# =============================================================================

def run_backtest():
    print("--- Step 3: Running Backtest Engine ---")
    
    # Path to the processed Arrow files
    spy_arrow = os.path.join(CONFIG["PROCESSED_DIR"], f"{CONFIG['TICKER']}.arrow")
    opt_arrow = os.path.join(CONFIG["PROCESSED_DIR"], f"{CONFIG['TICKER']}_OPT.arrow")
    
    # 1. Init Data Handler
    data_map = {
        CONFIG["TICKER"]: spy_arrow,
        f"{CONFIG['TICKER']}_OPT": opt_arrow
    }
    dh = DataHandler(data_map)
    
    # 2. Init Portfolio & Execution
    # Note: Broker Execution Mode (WCS/BCS) would be passed here if your Broker supports it.
    # We will set the commission on the broker.
    portfolio = Portfolio(initial_capital=CONFIG["INITIAL_CAPITAL"])
    broker = Broker(dh, commission=CONFIG["COMMISSION_PER_CONTRACT"]) 
    exchange = OptionExchange(dh)
    
    # 3. Init Strategy
    strategy = MovingAverageOptionStrategy(dh, portfolio)
    
    # 4. Run Engine
    engine = BacktestEngine(dh, portfolio, strategy, broker, exchange)
    engine.run()
    
    return engine.history

def plot_results(history):
    print("--- Step 4: Plotting Portfolio Performance ---")
    
    if not history:
        print("No trades occurred or history is empty.")
        return

    # Convert list of dicts to DataFrame
    df = pl.DataFrame(history)
    pdf = df.to_pandas()
    
    plt.figure(figsize=(10, 6))
    plt.plot(pdf['time'], pdf['equity'], label='Portfolio Equity', color='green')
    
    # Draw initial capital line
    plt.axhline(y=CONFIG["INITIAL_CAPITAL"], color='r', linestyle='--', label='Initial Capital')
    
    plt.title(f"Strategy Performance: {CONFIG['TICKER']} Trend Following")
    plt.xlabel("Date")
    plt.ylabel("Equity ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # 1. Prepare Data (One-time ETL)
    prepare_data()
    
    # 2. Visualize the Underlying Data
    # Load just the stock arrow file to visualize
    stock_path = os.path.join(CONFIG["PROCESSED_DIR"], f"{CONFIG['TICKER']}.arrow")
    df_stock = pl.read_ipc(stock_path)
    plot_market_analysis(df_stock)
    
    # 3. Run Strategy
    history = run_backtest()
    
    # 4. Plot Results
    plot_results(history)