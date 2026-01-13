"""
02_load_display_option_volume.py

PURPOSE:
    This script demonstrates how to:
    1. Load "Messy" Option Data (handling headers like 'pcflag', 'k').
    2. Apply Value Mapping (converting 1 -> 'C', 0 -> 'P').
    3. Aggregate data (Summing Call vs Put Volume per Day).
    4. Visualize the resulting time series on a single chart.

USAGE:
    $ python examples/02_load_display_option_volume.py
"""

import os
import sys
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- PATH SETUP ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- FRAMEWORK IMPORTS ---
try:
    from src.data.loader import load_and_standardize, DataSourceConfig
except ImportError as e:
    print(f"\n[CRITICAL ERROR] Could not import from 'src'.\nError: {e}\n")
    exit(1)

# =============================================================================
# 1. USER CONFIGURATION
# =============================================================================

RAW_SOURCE_PATH = os.path.join(project_root, "data", "SAMPLEdailyoption.csv")
PROCESSED_DIR = os.path.join(project_root, "data", "processed")
TICKER_SYMBOL = "SAMPLE_OPT"

COLUMN_MAPPING = {
    "date_eod": "datetime",
    "ticker":   "symbol",
    "pcflag":   "option_type", 
    "k":        "strike",
    "date_mat": "expiry",
    "volume":   "volume",
    "oi":       "open_interest",
    "bid":      "bid",
    "ask":      "ask"
}

# NOTE: Loader converts columns to String before mapping keys.
VALUE_MAPPING = {
    "option_type": {
        "1": "C", 
        "0": "P"
    }
}

# =============================================================================
# 2. DATA LOADING LOGIC
# =============================================================================

def get_option_data():
    config = DataSourceConfig(
        name="OptionLoader",
        col_map=COLUMN_MAPPING,
        val_map=VALUE_MAPPING
    )

    try:
        df, metadata = load_and_standardize(
            symbol=TICKER_SYMBOL, 
            file_path=RAW_SOURCE_PATH, 
            config=config, 
            output_dir=PROCESSED_DIR
        )
    except Exception as e:
        raise RuntimeError(f"Loader failed.\nDetails: {e}")

    print(f"\n[INFO] Data Operation Complete.")
    print(f"       Source: {metadata['source'].upper()}")
    print(f"       Loaded: {metadata['path']}")
    
    return df

# =============================================================================
# 3. AGGREGATION LOGIC (UPDATED)
# =============================================================================

def calculate_daily_volume(df):
    """
    Separates Call and Put volume and aggregates them by date.
    """
    print("\n[INFO] Aggregating Volume (Calls vs Puts)...")
    
    if "datetime" not in df.columns or "volume" not in df.columns or "option_type" not in df.columns:
        print("[ERROR] Missing required columns ('datetime', 'volume', 'option_type').")
        return None

    # Polars Aggregation:
    # We use 'when-then-otherwise' inside the aggregation to pivot the data
    daily_vol = (
        df.group_by("datetime")
        .agg([
            pl.col("volume").filter(pl.col("option_type") == "C").sum().alias("call_vol"),
            pl.col("volume").filter(pl.col("option_type") == "P").sum().alias("put_vol"),
            pl.col("volume").sum().alias("total_vol") # Optional total
        ])
        .sort("datetime")
    )
    
    return daily_vol

# =============================================================================
# 4. VISUALIZATION LOGIC (UPDATED)
# =============================================================================

def plot_volume(df_agg):
    """
    Plots Call Volume and Put Volume on the same chart.
    """
    print("[INFO] Preparing Plot...")
    
    pdf = df_agg.to_pandas()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot Calls (Green)
    ax.plot(pdf["datetime"], pdf["call_vol"], 
            color='green', linewidth=1.5, label='Call Volume')
    
    # Plot Puts (Red)
    ax.plot(pdf["datetime"], pdf["put_vol"], 
            color='red', linewidth=1.5, label='Put Volume')
    
    # Formatting
    ax.set_title(f"{TICKER_SYMBOL} - Daily Call vs Put Volume")
    ax.set_ylabel("Volume (Contracts)")
    ax.set_xlabel("Date")
    ax.legend() # Shows the labels defined in ax.plot
    ax.grid(True, alpha=0.3)

    # Date Axis Formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    print("[INFO] Displaying Plot...")
    plt.show()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=== 02_load_display_option_volume.py Started ===")
    
    # 1. Load Data
    try:
        df_chain = get_option_data()
    except Exception as e:
        print(f"[FATAL] {e}")
        exit(1)
        
    # 2. Inspect Raw Data
    print("\n--- RAW DATA INSPECTION ---")
    print(df_chain.head(3))
    
    # 3. Process Data
    df_vol = calculate_daily_volume(df_chain)
    print("\n--- AGGREGATED DATA ---")
    print(df_vol.head(3))

    # 4. Plot
    if df_vol is not None:
        plot_volume(df_vol)
        
    print("=== Done ===")