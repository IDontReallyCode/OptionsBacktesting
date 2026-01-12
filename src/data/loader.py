import polars as pl
from pathlib import Path
import os

def load_and_cache_symbol(symbol: str, csv_path: str) -> pl.DataFrame:
    """
    Smart loader:
    1. Checks if a compiled .arrow file exists (fast).
    2. If not, reads the .csv (slow), sorts it, and saves an .arrow file for next time.
    3. Returns the Polars DataFrame.
    """
    path_obj = Path(csv_path)
    ipc_path = path_obj.with_suffix(".arrow")

    # A. FAST PATH: Load Cached IPC
    if ipc_path.exists():
        print(f"[{symbol}] Loading cached data from {ipc_path.name}...")
        try:
            # memory_map=True is the key to C-like speed. 
            # It maps the file directly into virtual memory without copying.
            return pl.read_ipc(ipc_path, memory_map=True)
        except Exception as e:
            print(f"Warning: Cache file corrupted ({e}). Re-generating...")

    # B. SLOW PATH: Parse CSV
    print(f"[{symbol}] Parsing raw CSV (One-time setup)...")
    if not path_obj.exists():
        raise FileNotFoundError(f"Cannot find source file: {csv_path}")

    try:
        # Polars CSV reader is multi-threaded by default
        df = pl.read_csv(
            path_obj, 
            try_parse_dates=True, # Critical for time-series
            ignore_errors=True    # Skip bad lines instead of crashing
        )
        
        # 1. Ensure Chronological Order (Critical for backtesting)
        if "datetime" in df.columns:
            df = df.sort("datetime")
        
        # 2. Optimize Data Types (Optional but good for RAM)
        # Convert 64-bit floats to 32-bit if you want to save 50% RAM
        # df = df.with_columns(pl.col(pl.Float64).cast(pl.Float32))

        # 3. Save Cache
        print(f"[{symbol}] Saving cache to .arrow...")
        df.write_ipc(ipc_path)
        
        return df

    except Exception as e:
        raise IOError(f"Failed to ingest {symbol}: {e}")