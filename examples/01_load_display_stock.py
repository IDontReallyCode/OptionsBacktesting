"""
01_load_display_stock.py

PURPOSE:
    This script serves two key roles for users and developers:
    1. **Tutorial (Level 1):** A step-by-step guide demonstrating how to ingest raw CSV 
       stock data, map it to the engine's internal format, and visualize it.
    2. **Integration Verification:** A "real data" test to ensure the framework correctly 
       handles market data quirks (custom headers, date formats) before you attempt 
       complex backtesting.

    It bridges the gap between basic unit tests and full strategy implementation, 
    allowing you to verify your data pipeline is solid.

USAGE:
    Run this script from the terminal to generate a time-series plot of your stock data:
    $ python examples/01_load_display_stock.py

    (Ensure your terminal is at the root of the project so python can find 'src')
"""

import os
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- FRAMEWORK IMPORTS ---
# We wrap this in a try-except to give a clear error if the python path is wrong
try:
    from src.data.loader import load_and_standardize, DataSourceConfig
except ImportError as e:
    print("\n[CRITICAL ERROR] Could not import from 'src'.")
    print("Ensure you are running this script from the project root.")
    print(f"Error details: {e}\n")
    exit(1)

# =============================================================================
# 1. USER CONFIGURATION
# =============================================================================

# [INSTRUCTION]: Change this to the path of your raw CSV file.
RAW_SOURCE_PATH = "data/SAMPLEdailystock.csv"

# [INSTRUCTION]: Change this to the folder where you want Arrow files saved.
PROCESSED_DIR = "data/processed"

# [INSTRUCTION]: The ticker symbol used for naming the output file (e.g., "SAMPLE.arrow")
TICKER_SYMBOL = "SAMPLE"

# [INSTRUCTION]: Define which column you want to plot (Internal Name).
# Standard names are usually: 'close', 'open', 'high', 'low', 'volume'.
PLOT_COLUMN = "close"

# [INSTRUCTION]: COLUMN MAPPING
# This is crucial. Map your CSV headers (Left) to the Engine's expected names (Right).
# Engine expects: 'datetime', 'open', 'high', 'low', 'close', 'volume'.
COLUMN_MAPPING = {
    "date_eod": "datetime",  # Your CSV has 'date_eod', engine needs 'datetime'
    "open": "open",
    "high": "high",
    "low": "low",            # If your CSV lacks 'low', map 'close' or 'open' to 'low' as fallback
    "close": "close",
    "volume": "volume"
}

# =============================================================================
# 2. DATA LOADING LOGIC
# =============================================================================

def get_stock_data():
    """
    Orchestrates the data loading. 
    Now relies on loader.py to handle the Cache (Fast Path) vs Processing (Slow Path).
    """
    
    # 1. Create the Config Object
    # This defines how to map 'date_eod' -> 'datetime', etc.
    config = DataSourceConfig(
        name="StockLoader",
        col_map=COLUMN_MAPPING
    )

    # 2. Call the Loader
    # It now returns a tuple: (DataFrame, Metadata_Dict)
    # The loader itself checks if the Arrow file exists.
    try:
        df, metadata = load_and_standardize(
            symbol=TICKER_SYMBOL, 
            file_path=RAW_SOURCE_PATH, 
            config=config, 
            output_dir=PROCESSED_DIR
        )
    except Exception as e:
        # Wrap loader errors with a helpful message
        raise RuntimeError(f"Loader failed to get data for {TICKER_SYMBOL}.\nDetails: {e}")

    # 3. Display Metadata (The "Flag" you asked for)
    print(f"\n[INFO] Data Operation Complete.")
    print(f"       Source: {metadata['source'].upper()}")  # 'CACHE' or 'RAW'
    print(f"       Loaded: {metadata['path']}")
    
    return df


# =============================================================================
# 3. VISUALIZATION LOGIC
# =============================================================================

def plot_time_series(df, col_name):
    """
    Simple Matplotlib visualization of the Time Series with formatted dates.
    """
    print(f"\n[INFO] Preparing plot for column: '{col_name}'...")

    # 1. Validation: Does the column exist?
    if col_name not in df.columns:
        print(f"[ERROR] Column '{col_name}' not found in data!")
        print(f"Available columns: {df.columns}")
        print("Check your 'COLUMN_MAPPING' in the Configuration section.")
        return

    # 2. Sort by date (Critical for line charts)
    if "datetime" in df.columns:
        df = df.sort("datetime")
    else:
        print("[WARN] 'datetime' column missing. Plot might be unordered.")

    # 3. Convert to Pandas for Plotting
    # Note: Polars converts its datetime types to Pandas timestamps automatically
    pdf = df.to_pandas()

    # 4. Plot
    # We use 'fig, ax' syntax here for better control over axis formatting
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Check if we have dates for the X-axis
    if "datetime" in pdf.columns:
        ax.plot(pdf["datetime"], pdf[col_name], label=col_name, linewidth=1, color='blue')
        ax.set_xlabel("Date")
        
        # --- DATE FORMATTING MAGIC ---
        # 1. Set the format (e.g., 2021-01)
        # You can change '%Y-%m-%d' to '%Y-%m' if you want less clutter
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 2. Auto-locate reasonable ticks (avoids showing every single day)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # 3. Rotate and align the dates nicely to prevent overlap
        fig.autofmt_xdate()
        # -----------------------------
    else:
        # Fallback to index if no date found
        ax.plot(pdf.index, pdf[col_name], label=col_name, linewidth=1, color='blue')
        ax.set_xlabel("Index")

    ax.set_title(f"{TICKER_SYMBOL} - {col_name.upper()} Price History")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    print("[INFO] Displaying plot window...")
    plt.show()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=== 01_load_display_stock.py Started ===")
    
    # 1. Load
    try:
        df = get_stock_data()
    except Exception as e:
        print(f"\n[FATAL] Failed to load data. Error:\n{e}")
        exit(1)

    # 2. Inspect (Debug Step)
    print("\n--- DATA INSPECTION ---")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns}")
    print(df.head(3))
    print("-----------------------\n")

    # 3. Plot
    plot_time_series(df, PLOT_COLUMN)
    
    print("=== Done ===")