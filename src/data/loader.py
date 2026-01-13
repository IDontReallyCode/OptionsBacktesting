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

# ... imports stay the same ...

def load_and_standardize(
    symbol: str, 
    file_path: str, 
    config: Union[DataSourceConfig, dict],
    output_dir: str = None,
    force_reload: bool = False
) -> tuple[pl.DataFrame, dict]:  # <--- CHANGED RETURN TYPE
    """
    Loads data and returns (DataFrame, Metadata).
    Metadata contains info like {'source': 'cache'|'raw', 'path': ...}
    """
    
    # 0. Setup Output Path
    out_path = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{symbol}.arrow")

    # 1. Check Cache (FAST PATH)
    if out_path and os.path.exists(out_path) and not force_reload:
        print(f"[LOADER] Found cached data for {symbol}.")
        try:
            df = pl.read_ipc(out_path)
            # RETURN CACHE + METADATA
            return df, {"source": "cache", "path": out_path} 
        except Exception as e:
            print(f"[WARN] Cache corrupted ({e}). Re-processing...")

    print(f"[LOADER] Processing Raw Data for {symbol}...")
    
    # 2. Normalize Config
    if isinstance(config, dict):
        mapping = config.get("col_map", config)
        val_mapping = config.get("val_map", {})
    else:
        mapping = config.col_map
        val_mapping = config.val_map

    # 3. Read CSV
    try:
        df = pl.read_csv(file_path, try_parse_dates=True, ignore_errors=True)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV at {file_path}. Error: {e}")

    # 4. Apply Column Renaming
    existing_cols = set(df.columns)
    valid_mapping = {k: v for k, v in mapping.items() if k in existing_cols}
    
    if valid_mapping:
        print(f"[LOADER] Renaming columns: {valid_mapping}")
        df = df.rename(valid_mapping)

    # 5. Standardize Date Column
    if "datetime" in df.columns:
        if df["datetime"].dtype == pl.Utf8:
            df = df.with_columns(
                pl.col("datetime").str.strptime(pl.Datetime, "%Y-%m-%d", strict=False)
            )
        df = df.sort("datetime")

    # 6. Apply Value Mapping
    for col_name, map_dict in val_mapping.items():
        if col_name in df.columns:
            df = df.with_columns(
                pl.col(col_name).cast(pl.Utf8).replace(map_dict)
            )

    # 7. Save to Arrow
    if out_path:
        df.write_ipc(out_path)
        print(f"[LOADER] Saved processed data to: {out_path}")

    # RETURN PROCESSED + METADATA
    return df, {"source": "raw", "path": file_path}