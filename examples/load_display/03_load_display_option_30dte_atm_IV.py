"""
03_load_display_option_30dte_atm_IV.py

PURPOSE:
    Advanced Data Processing:
    1. JOINS Stock Data (Underlying Price) with Option Data.
    2. Implements a "Constant Maturity" algorithm:
       - Finds Expirations bracketing 30 Days (e.g., 20 DTE and 35 DTE).
       - Finds Strikes bracketing the Underlying Price (ATM).
    3. Interpolates IV to generate a continuous "30-Day ATM IV" index.

    This mimics how indices like VIX are constructed (simplified).

USAGE:
    $ python examples/03_load_display_option_30dte_atm_IV.py
"""

import os
import sys
import numpy as np
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
    print(f"\n[CRITICAL ERROR] Could not import from 'src'. {e}\n")
    exit(1)

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

TICKER = "SAMPLE"
STOCK_PATH = os.path.join(project_root, "data", "SAMPLEdailystock.csv")
OPTION_PATH = os.path.join(project_root, "data", "SAMPLEdailyoption.csv")
PROCESSED_DIR = os.path.join(project_root, "data", "processed")

# Stock Config (reuse from 01)
STOCK_MAP = {
    "date_eod": "datetime",
    "close": "underlying_price" # Map directly to standard name
}

# Option Config (reuse from 02)
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
# 2. DATA LOADING & MERGING
# =============================================================================

def load_merged_data():
    """
    Loads Stock and Option data independently, then joins them.
    Returns: A joined DataFrame with 'underlying_price' attached to every option row.
    """
    print("\n[INFO] Loading Stock Data...")
    df_stock, _ = load_and_standardize(
        TICKER, STOCK_PATH, DataSourceConfig("Stock", STOCK_MAP), PROCESSED_DIR
    )
    
    # We only need Date and Price from stock
    df_stock = df_stock.select(["datetime", "underlying_price"])

    print("\n[INFO] Loading Option Data...")
    df_opt, _ = load_and_standardize(
        f"{TICKER}_OPT", OPTION_PATH, 
        DataSourceConfig("Opt", OPTION_MAP, OPTION_VAL_MAP), PROCESSED_DIR
    )

    print("\n[INFO] Joining Stock Price to Option Chains...")
    # Join on Date so we know the spot price for every option row
    df_merged = df_opt.join(df_stock, on="datetime", how="inner")
    
    return df_merged

# =============================================================================
# 3. 30-DAY ATM LOGIC
# =============================================================================

def calculate_30d_iv(df):
    """
    Calculates the 30-Day Interpolated ATM IV for Calls and Puts.
    Uses Python iteration for clarity on the "Bracketing" logic.
    """
    print("\n[INFO] Calculating 30-Day ATM IV (This may take a moment)...")

    # Filter for valid data first
    # 1. IV must be > 0
    # 2. DTE must be reasonable (e.g., between 5 and 60 to bracket 30)
    df = df.filter(
        (pl.col("iv") > 0) & 
        (pl.col("dte") > 5) & 
        (pl.col("dte") < 90)
    )

    # Convert to pandas for easier iteration over dates/groups
    # (Polars is faster, but the logic for bracketing is very complex to write in expressions)
    pdf = df.to_pandas()
    
    results = []
    
    # Group by Date and Option Type (C/P)
    grouped = pdf.groupby(["datetime", "option_type"])
    
    for (date, opt_type), group in grouped:
        spot = group["underlying_price"].iloc[0]
        
        # --- A. Find Time Bracket (DTEs around 30) ---
        # Get unique DTEs available today
        unique_dtes = np.sort(group["dte"].unique())
        
        # Split into those < 30 and those > 30
        below_30 = unique_dtes[unique_dtes <= 30]
        above_30 = unique_dtes[unique_dtes > 30]
        
        # We need at least one on each side, or closest match
        if len(below_30) == 0 or len(above_30) == 0:
            continue # Cannot interpolate
            
        dte_1 = below_30[-1] # Closest DTE <= 30
        dte_2 = above_30[0]  # Closest DTE > 30
        
        # --- B. Calculate ATM IV for DTE 1 ---
        iv_1 = _get_atm_iv_for_dte(group, dte_1, spot)
        
        # --- C. Calculate ATM IV for DTE 2 ---
        iv_2 = _get_atm_iv_for_dte(group, dte_2, spot)
        
        if np.isnan(iv_1) or np.isnan(iv_2):
            continue

        # --- D. Linear Interpolation to 30 Days ---
        # Formula: IV_30 = IV_1 + (IV_2 - IV_1) * (30 - DTE_1) / (DTE_2 - DTE_1)
        # Weight based on time distance
        if dte_2 == dte_1:
            iv_30 = iv_1
        else:
            time_weight = (30 - dte_1) / (dte_2 - dte_1)
            iv_30 = iv_1 + time_weight * (iv_2 - iv_1)
            
        results.append({
            "datetime": date,
            "option_type": opt_type,
            "iv30": iv_30,
            "underlying": spot
        })

    return pl.DataFrame(results)

def _get_atm_iv_for_dte(df_slice, target_dte, spot_price):
    """
    Helper: Given rows for a specific DTE, find the 2 strikes surrounding Spot Price
    and average their IV.
    """
    # Filter for just this DTE
    d_slice = df_slice[df_slice["dte"] == target_dte]
    
    # Sort by strike
    d_slice = d_slice.sort_values("strike")
    strikes = d_slice["strike"].values
    ivs = d_slice["iv"].values
    
    # Find insertion point for spot price
    idx = np.searchsorted(strikes, spot_price)
    
    # Handle Edge Cases (Spot outside strike range)
    if idx == 0 or idx == len(strikes):
        return np.nan # Cannot bracket
        
    # Get Bracket Strikes: idx-1 (Below) and idx (Above)
    iv_low = ivs[idx-1]
    iv_high = ivs[idx]
    
    # Simple Average of the two ATM strikes
    # (Refinement: Could weight by distance to strike, but simple avg is standard)
    return (iv_low + iv_high) / 2.0

# =============================================================================
# 4. VISUALIZATION
# =============================================================================

def plot_iv_term_structure(df):
    print("[INFO] Plotting 30-Day Constant Maturity IV...")
    
    pdf = df.to_pandas()
    
    # Pivot for plotting: columns = [C, P], index = datetime
    pivot = pdf.pivot(index="datetime", columns="option_type", values="iv30")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Plot 1: IV
    ax1.plot(pivot.index, pivot["C"], color='green', label='Call 30d IV', linewidth=1.5)
    ax1.plot(pivot.index, pivot["P"], color='red', label='Put 30d IV', linewidth=1.5, linestyle='--')
    ax1.set_title(f"{TICKER} - 30-Day ATM Implied Volatility (Interpolated)")
    ax1.set_ylabel("Implied Volatility")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Underlying Price (Context)
    # We take the mean underlying per date (it's constant per date anyway)
    prices = pdf.groupby("datetime")["underlying"].mean()
    ax2.plot(prices.index, prices.values, color='black', label='Stock Price')
    ax2.set_title("Underlying Price Context")
    ax2.set_ylabel("Price")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Date Formatting
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    
    plt.tight_layout()
    plt.show()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=== 03_load_display_option_30dte_atm_IV.py Started ===")
    
    # 1. Load & Join
    try:
        df_raw = load_merged_data()
    except Exception as e:
        print(f"[FATAL] {e}")
        exit(1)

    # 2. Process (Interpolate 30D IV)
    df_iv30 = calculate_30d_iv(df_raw)
    
    print("\n[RESULT] 30-Day ATM IV Data:")
    print(df_iv30.head())

    # 3. Plot
    if not df_iv30.is_empty():
        plot_iv_term_structure(df_iv30)
    else:
        print("[WARN] No data resulted from calculation (Check DTE/IV filters).")

    print("=== Done ===")