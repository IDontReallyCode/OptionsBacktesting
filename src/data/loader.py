"""
Data Loader Module
==================

Responsibility:
    1. Ingest "Messy" CSVs from various vendors (CBOE, OptionMetrics, etc.).
    2. Normalize column names (e.g., "CPFlag" -> "option_type").
    3. Normalize values (e.g., "Call" -> "C", True -> "C").
    4. Optimize Memory: Downcast types to smallest safe representation.
    5. Cache: Save as Memory-Mapped Arrow (IPC) files for instant reloading.

Memory Optimizations:
    - Strings (Symbol, Option Type): Converted to `pl.Categorical`. 
      (Reduces memory usage by ~8x compared to standard strings).
    - Volume: Converted to `pl.UInt32` (4 bytes vs standard 8 bytes).
    - Float64: Kept for prices to ensure precision (avoid penny-rounding errors).
"""

import polars as pl
from pathlib import Path
from typing import Dict, Optional, Union
from dataclasses import dataclass, field
import os

# --- 1. CONFIGURATION CLASSES ---

@dataclass
class DataSourceConfig:
    """
    Defines how to translate a specific vendor's format into our Internal Standard.
    """
    name: str
    
    # Map Vendor Column -> Internal Standard Column
    col_map: Dict[str, str]

    # Map Vendor Values -> Internal Standard Values
    val_map: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # Date Format string (e.g. "%Y-%m-%d") if the CSV is weird. None = Auto-detect.
    date_fmt: Optional[str] = None

# --- 2. VENDOR PRESETS ---

CBOE_CONFIG = DataSourceConfig(
    name="CBOE",
    col_map={
        "quote_datetime": "datetime",
        "root": "symbol",
        "underlying_last": "underlying_price",
        "strike": "strike",
        "expiration": "expiry",
        "bid": "bid",
        "ask": "ask",
        "volume": "volume",
        "type": "option_type"
    },
    val_map={
        "option_type": {"Call": "C", "Put": "P", "call": "C", "put": "P", "C": "C", "P": "P"}
    }
)

OPTION_METRICS_CONFIG = DataSourceConfig(
    name="OPTION_METRICS",
    col_map={
        "date": "datetime",
        "symbol": "symbol",
        "underlying_price": "underlying_price",
        "strike_price": "strike",
        "exdate": "expiry",
        "best_bid": "bid",
        "best_offer": "ask",
        "volume": "volume", 
        "cp_flag": "option_type"
    },
    val_map={
        "option_type": {"call": "C", "put": "P", "C": "C", "P": "P"} 
    }
)

SCHWAB_CONFIG = DataSourceConfig(
    name="SCHWAB",
    col_map={
        "Timestamp": "datetime",
        "Symbol": "symbol",
        "UnderlyingPrice": "underlying_price",
        "Strike": "strike",
        "ExpDate": "expiry",
        "Bid": "bid",
        "Ask": "ask",
        "LastSize": "volume",
        "CallPut": "option_type" 
    },
    val_map={
        "option_type": {"Call": "C", "Put": "P", "c": "C", "p": "P"}
    }
)

# --- 3. CORE LOGIC ---

def load_and_standardize(
    symbol: str, 
    raw_path: str, 
    config: Union[DataSourceConfig, Dict],
    output_dir: str = "data",
    force_reload: bool = False
) -> pl.DataFrame:
    """
    Reads a raw CSV, applies the config mapping, optimizes types, and saves a standardized .arrow file.
    
    Args:
        symbol: Ticker symbol (e.g. "SPY").
        raw_path: Path to the raw CSV file.
        config: Either a DataSourceConfig object OR a simple dictionary mapping.
        output_dir: Folder where the processed .arrow file will be saved.
        force_reload: If True, ignores existing cache and re-processes.
    """
    
    # ---------------------------------------------------------
    # 0. SETUP PATHS & CONFIG
    # ---------------------------------------------------------
    
    # Compatibility: If user passed a simple dict (like in detailed_example.py), wrap it.
    if isinstance(config, dict):
        config = DataSourceConfig(name="Generic", col_map=config)

    raw_path_obj = Path(raw_path)
    out_dir_obj = Path(output_dir)
    
    # Create output directory if it doesn't exist
    if not out_dir_obj.exists():
        out_dir_obj.mkdir(parents=True, exist_ok=True)
        
    # Define the destination Arrow file path
    ipc_path = out_dir_obj / f"{symbol}.arrow"

    # ---------------------------------------------------------
    # 1. FAST PATH: Load Cache
    # ---------------------------------------------------------
    if ipc_path.exists() and not force_reload:
        print(f"[{symbol}] Loading standardized cache from: {ipc_path}")
        try:
            return pl.read_ipc(ipc_path, memory_map=True)
        except Exception as e:
            print(f"[{symbol}] Cache corrupted ({e}). Re-processing...")

    # ---------------------------------------------------------
    # 2. SLOW PATH: Ingest and Normalize
    # ---------------------------------------------------------
    print(f"[{symbol}] Ingesting Raw Data from {raw_path}...")
    
    if not raw_path_obj.exists():
        raise FileNotFoundError(f"Source file not found: {raw_path}")

    # Use Scan (Lazy) to handle massive files without blowing RAM
    lf = pl.scan_csv(
        raw_path_obj, 
        try_parse_dates=True, 
        ignore_errors=True
    )

    # A. Rename Columns
    existing_cols = lf.collect_schema().names()
    
    # Filter map to only include columns that actually exist in this file
    valid_renames = {k: v for k, v in config.col_map.items() if k in existing_cols}
    
    if valid_renames:
        lf = lf.rename(valid_renames)

    # B. Value Normalization (e.g. "Call" -> "C")
    for col_name, mapping in config.val_map.items():
        if col_name in valid_renames.values():
            lf = lf.with_columns(
                pl.col(col_name).cast(pl.Utf8).replace(mapping)
            )

    # ---------------------------------------------------------
    # 3. MEMORY OPTIMIZATION & TYPE CASTING
    # ---------------------------------------------------------
    
    current_cols = valid_renames.values()

    # 1. Option Type: Categorical is huge memory saver vs String
    if "option_type" in current_cols:
        lf = lf.with_columns(pl.col("option_type").cast(pl.Categorical))

    # 2. Symbol: Categorical saves memory if many rows share the same symbol
    if "symbol" in current_cols:
        lf = lf.with_columns(pl.col("symbol").cast(pl.Categorical))

    # 3. Volume: UInt32 (0 to 4 billion) is sufficient and saves 50% vs Int64
    if "volume" in current_cols:
        lf = lf.with_columns(pl.col("volume").fill_null(0).cast(pl.UInt32))

    # 4. Prices: Float64 is safer for financial math than Float32
    price_cols = ["strike", "underlying_price", "bid", "ask", "open", "high", "low", "close"]
    for p_col in price_cols:
        if p_col in current_cols:
            lf = lf.with_columns(pl.col(p_col).cast(pl.Float64))

    # 5. Sorting (Crucial for Time-Series Replay)
    if "datetime" in current_cols:
        lf = lf.sort("datetime")

    # 6. Calculate Midpoint (Helper)
    if "bid" in current_cols and "ask" in current_cols:
        lf = lf.with_columns(
            ((pl.col("bid") + pl.col("ask")) / 2.0).alias("mid")
        )

    # ---------------------------------------------------------
    # 4. EXECUTE AND CACHE
    # ---------------------------------------------------------
    try:
        df = lf.collect()
        
        # Ensure 'datetime' exists, if not try to find 'date' and rename it
        if "datetime" not in df.columns and "date" in df.columns:
            df = df.rename({"date": "datetime"})

        print(f"[{symbol}] Saving cache ({df.height} rows) to {ipc_path}...")
        df.write_ipc(ipc_path)
        return df
        
    except Exception as e:
        raise RuntimeError(f"Failed to standardize {symbol}: {e}")