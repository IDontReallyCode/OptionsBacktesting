"""
02_load_display_option_volume.py

PURPOSE:
    This script demonstrates how to:
    1. Load "Messy" Option Data (handling headers like 'pcflag', 'k').
    2. Apply Value Mapping (converting 1 -> 'C', 0 -> 'P').
    3. Aggregate data (Summing Total Volume per Day).
    4. Visualize the resulting time series.

    It serves as a test for the 'val_map' feature of the loader and 
    Polars aggregation syntax.

USAGE:
    $ python examples/02_load_display_option_volume.py
"""

import os
import sys
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- PATH SETUP ---
# Ensures we can import 'src' even if running from the 'examples/' folder
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

# [INSTRUCTION]: Path to your raw Option CSV.
RAW_SOURCE_PATH = os.path.join(project_root, "data", "SAMPLEdailyoption.csv")

# [INSTRUCTION]: Output folder for the processed Arrow file.
PROCESSED_DIR = os.path.join(project_root, "data", "processed")

# [INSTRUCTION]: Ticker Symbol (Used for file naming).
TICKER_SYMBOL = "SAMPLE_OPT"

# [INSTRUCTION]: COLUMN MAPPING
# Map your CSV headers (Left) to the Internal Standard (Right).
# Internal Standard: 'datetime', 'symbol', 'strike', 'expiry', 'option_type', 'volume', 'open_interest'
COLUMN_MAPPING = {
    "date_eod": "datetime",
    "ticker":   "symbol",
    "pcflag":   "option_type",  # We will map values for this later (1->C, 0->P)
    "k":        "strike",
    "date_mat": "expiry",
    "volume":   "volume",
    "oi":       "open_interest",
    "bid":      "bid",
    "ask":      "ask"
}

# [INSTRUCTION]: VALUE MAPPING
# Map specific values inside a column. 
# Here we convert the integer flag to a standard string char.
# NOTE: The loader converts the column to String before mapping, so keys must be strings ("1", not 1).
VALUE_MAPPING = {
    "option_type": {
        "1": "C",  # Assuming 1 = Call
        "0": "P"   # Assuming 0 = Put
    }
}

# =============================================================================
# 2. DATA LOADING LOGIC
# =============================================================================

def get_option_data():
    """
    Loads option data using the robust loader, handling caching automatically.
    """
    # 1. Create Config
    config = DataSourceConfig(
        name="OptionLoader",
        col_map=COLUMN_MAPPING,
        val_map=VALUE_MAPPING  # <--- Passing the value map here
    )

    # 2. Load
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
# 3. AGGREGATION LOGIC
# =============================================================================

def calculate_daily_volume(df):
    """
    Aggregates the detailed option chain to find Total Volume per Day.
    """
    print("\n[INFO] Aggregating Volume by Date...")
    
    # Check if we have the required columns
    if "datetime" not in df.columns or "volume" not in df.columns:
        print("[ERROR] Cannot calculate volume. Missing 'datetime' or 'volume' columns.")
        return None

    # Polars Aggregation:
    # 1. Group By Date
    # 2. Sum the Volume column
    # 3. Sort by Date
    daily_vol = (
        df.group_by("datetime")
        .agg(pl.col("volume").sum().alias("total_volume"))
        .sort("datetime")
    )
    
    return daily_vol

# =============================================================================
# 4. VISUALIZATION LOGIC
# =============================================================================

def plot_volume(df_agg):
    """
    Plots the Total Daily Volume.
    """
    print("[INFO] Preparing Plot...")
    
    # Convert to Pandas for Matplotlib
    pdf = df_agg.to_pandas()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Bar chart usually looks better for Volume, but Line is fine too.
    # We'll use a filled area chart (plot + fill_between) for a pro look.
    ax.plot(pdf["datetime"], pdf["total_volume"], color='#1f77b4', linewidth=1.5, label='Total Option Volume')
    ax.fill_between(pdf["datetime"], pdf["total_volume"], color='#1f77b4', alpha=0.3)
    
    # Formatting
    ax.set_title(f"{TICKER_SYMBOL} - Total Daily Option Volume")
    ax.set_ylabel("Volume (Contracts)")
    ax.set_xlabel("Date")
    ax.legend()
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
        
    # 2. Inspect Raw Data (Sanity Check)
    print("\n--- RAW DATA INSPECTION ---")
    print(df_chain.head(3))
    print(f"Columns: {df_chain.columns}")
    
    # Verify mapping worked (Check if 'option_type' has 'C'/'P' or '1'/'0')
    if "option_type" in df_chain.columns:
        unique_types = df_chain["option_type"].unique().to_list()
        print(f"Unique Option Types found: {unique_types} (Should be ['C', 'P'])")

    # 3. Process Data
    df_vol = calculate_daily_volume(df_chain)

    # 4. Plot
    if df_vol is not None:
        plot_volume(df_vol)
        
    print("=== Done ===")