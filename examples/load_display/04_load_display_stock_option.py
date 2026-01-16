"""
04_load_display_stock_option.py

PURPOSE:
    Demonstrates a complete "Multi-Source" pipeline:
    1. Loads STOCK data (Long history).
    2. Loads OPTION data (Often shorter history).
    3. Calculates a complex metric (30-Day ATM IV) that requires bridging both datasets.
       - Needs Stock Price to find "At-The-Money" (ATM).
       - Needs Option Chain to find Implied Volatility (IV).
    4. Visualizes them on a synchronized dual-axis plot, handling mismatched date ranges.

    This is the standard pattern for feature engineering in backtesting:
    combining asset price history with derived option metrics.

USAGE:
    $ python examples/04_load_display_stock_option.py
"""

import os
import sys
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- PATH SETUP ---
# Allows importing 'src' from the examples folder
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- IMPORTS ---
try:
    from src.data.loader import load_and_standardize, DataSourceConfig
except ImportError as e:
    print(f"\n[CRITICAL ERROR] Could not import from 'src'. {e}\n")
    exit(1)

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

TICKER = "SAMPLE"
PROCESSED_DIR = os.path.join(project_root, "data", "processed")

# --- Stock Config ---
STOCK_PATH = os.path.join(project_root, "data", "SAMPLEdailystock.csv")
STOCK_MAP = {
    "date_eod": "datetime",
    "close": "underlying_price"
}

# --- Option Config ---
OPTION_PATH = os.path.join(project_root, "data", "SAMPLEdailyoption.csv")
OPTION_MAP = {
    "date_eod": "datetime",
    "ticker": "symbol",
    "pcflag": "option_type",
    "k": "strike",
    "dte": "dte",
    "iv": "iv"
}
OPTION_VAL_MAP = {"option_type": {"1": "C", "0": "P"}}


# =============================================================================
# 2. DATA LOADING
# =============================================================================

def get_stock_data():
    """
    Loads the underlying stock data (The "Fast" or "Slow" path is handled by loader.py).
    """
    config = DataSourceConfig(name="Stock", col_map=STOCK_MAP)
    try:
        df, meta = load_and_standardize(TICKER, STOCK_PATH, config, PROCESSED_DIR)
        print(f"[INFO] Stock Data Loaded ({meta['source']}). Rows: {len(df)}")
        return df
    except Exception as e:
        raise RuntimeError(f"Stock load failed: {e}")

def get_option_data():
    """
    Loads the raw option chains.
    """
    config = DataSourceConfig(name="Option", col_map=OPTION_MAP, val_map=OPTION_VAL_MAP)
    try:
        df, meta = load_and_standardize(f"{TICKER}_OPT", OPTION_PATH, config, PROCESSED_DIR)
        print(f"[INFO] Option Data Loaded ({meta['source']}). Rows: {len(df)}")
        return df
    except Exception as e:
        raise RuntimeError(f"Option load failed: {e}")


# =============================================================================
# 3. COMPLEX METRIC CALCULATION (IV 30)
# =============================================================================

def calculate_atm_iv30(df_stock, df_opt):
    """
    Calculates a 30-day constant maturity Implied Volatility (IV) for the ATM strike.
    
    Steps:
    1. Inner Join Stock + Options (We need Stock Price to know what 'ATM' is).
    2. Filter for Call options only (for simplicity in this example).
    3. Bracket 30 Days: Find DTEs just below and just above 30.
    4. Interpolate IV between them.
    """
    print("\n[INFO] Calculating 30-Day ATM IV...")

    # 1. Join to get Spot Price attached to every option row
    #    Note: This is an inner join, so it only calculates where we have BOTH data points.
    combined = df_opt.join(df_stock, on="datetime", how="inner")
    
    # 2. Pre-filter (Valid IV, reasonable DTEs, Calls only for this demo)
    combined = combined.filter(
        (pl.col("iv") > 0) & 
        (pl.col("dte") > 5) & 
        (pl.col("dte") < 90) &
        (pl.col("option_type") == "C")
    )
    
    # We switch to Pandas for the complex "bracketing" iteration
    pdf = combined.to_pandas()
    results = []

    # Group by Date to process one day at a time
    for date, group in pdf.groupby("datetime"):
        spot = group["close"].iloc[0]
        
        # A. Bracket Time (DTE < 30 and DTE > 30)
        dtes = np.sort(group["dte"].unique())
        below = dtes[dtes <= 30]
        above = dtes[dtes > 30]
        
        if len(below) == 0 or len(above) == 0:
            continue # Cannot interpolate
            
        dte1, dte2 = below[-1], above[0]
        
        # B. Get ATM IV for those two DTEs
        iv1 = _get_atm_iv(group, dte1, spot)
        iv2 = _get_atm_iv(group, dte2, spot)
        
        if np.isnan(iv1) or np.isnan(iv2):
            continue
            
        # C. Interpolate to 30 Days
        if dte2 == dte1:
            iv30 = iv1
        else:
            weight = (30 - dte1) / (dte2 - dte1)
            iv30 = iv1 + weight * (iv2 - iv1)
            
        results.append({"datetime": date, "iv30": iv30})
        
    return pl.DataFrame(results)

def _get_atm_iv(group, dte, spot):
    """Helper: Finds two strikes around spot price and averages their IV."""
    slice_df = group[group["dte"] == dte].sort_values("strike")
    strikes = slice_df["strike"].values
    ivs = slice_df["iv"].values
    
    # Find where spot fits in the strikes
    idx = np.searchsorted(strikes, spot)
    if idx == 0 or idx == len(strikes):
        return np.nan
        
    # Average the IV of the strike below and above spot
    return (ivs[idx-1] + ivs[idx]) / 2.0


# =============================================================================
# 4. VISUALIZATION
# =============================================================================

def plot_synchronized_data(df_stock, df_iv):
    """
    Plots Stock Price (Left Axis) and IV (Right Axis).
    Handles the fact that df_stock might be much longer than df_iv.
    """
    print("[INFO] Generating Plot...")
    
    # Convert to pandas for Matplotlib
    p_stock = df_stock.sort("datetime").to_pandas()
    p_iv = df_iv.sort("datetime").to_pandas()
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # --- Axis 1: Stock Price (The "Long" Series) ---
    color1 = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Stock Price ($)', color=color1)
    ax1.plot(p_stock['datetime'], p_stock['close'], color=color1, linewidth=2, label=f"{TICKER} Price")
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.15)

    # --- Axis 2: 30D IV (The "Short" Series) ---
    # We create a twin axis sharing the same x-axis
    ax2 = ax1.twinx() 
    
    color2 = 'tab:orange'
    ax2.set_ylabel('30-Day ATM IV', color=color2)
    ax2.plot(p_iv['datetime'], p_iv['iv30'], color=color2, linewidth=1.5, linestyle='--', label="30D ATM IV")
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title & Formatting
    plt.title(f"{TICKER}: Price vs. Implied Volatility Regime")
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # Format Date Axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    
    plt.tight_layout()
    plt.show()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=== 04_load_display_stock_option.py Started ===\n")
    
    # 1. Load Disparate Data Sources
    try:
        stock_data = get_stock_data()   # e.g., 1000 days
        option_data = get_option_data() # e.g., 200 days
    except Exception as e:
        print(f"[FATAL] {e}")
        exit(1)
        
    # 2. Derive Option Metrics (Requires intersection of Stock & Option)
    #    The resulting dataframe will only exist where dates overlap.
    iv_data = calculate_atm_iv30(stock_data, option_data)
    
    if iv_data.is_empty():
        print("[WARN] No IV data calculated (Check DTE filters or date overlap).")
        exit(0)
        
    print(f"\n[INFO] IV Calculation Complete. Rows: {len(iv_data)}")
    print(f"[INFO] Note: Stock data has {len(stock_data)} rows, IV data has {len(iv_data)} rows.")

    # 3. Visualize
    #    Pass both to the plotter to handle the mismatched time series
    plot_synchronized_data(stock_data, iv_data)
    
    print("\n=== Done ===")