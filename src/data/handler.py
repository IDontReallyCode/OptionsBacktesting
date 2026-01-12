"""
Data Handler Module
===================

Responsibility:
    1. Load standardized .arrow files (created by loader.py).
    2. Synchronize timelines across multiple assets (Union of all timestamps).
    3. Serve data step-by-step (Bar-by-Bar) to the Backtest Engine.

Key Features:
    - Memory Mapping: Reads Arrow files instantly without copying to RAM.
    - Universal Timeline: Handles asynchronous data (e.g., Ticker A trades at 10:01, Ticker B at 10:02).
    - Lookahead Bias Prevention: Only serves data for the current timestamp.
"""

import polars as pl
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

class DataHandler:
    def __init__(self, file_map: Dict[str, str]):
        """
        Args:
            file_map: Dictionary mapping symbol -> path to .arrow file.
                      e.g. {"SPY": "data/spy.arrow", "SPY_OPT": "data/spy_opt.arrow"}
        """
        self.file_map = file_map
        self.data_store: Dict[str, pl.DataFrame] = {}
        self.timeline: List[datetime] = []
        
        # Iteration State
        self.time_idx: int = 0
        self.current_time: Optional[datetime] = None
        self.current_data_slice: Dict[str, pl.DataFrame] = {}
        self.continue_backtest: bool = True

        self._load_all_data()
        self._build_timeline()

    def _load_all_data(self):
        """Loads all arrow files into memory-mapped DataFrames."""
        for symbol, path in self.file_map.items():
            p = Path(path)
            if not p.exists():
                raise FileNotFoundError(f"Data file not found for {symbol}: {path}")
            
            # memory_map=True is crucial for performance on large files
            try:
                self.data_store[symbol] = pl.read_ipc(p, memory_map=True)
            except Exception as e:
                raise RuntimeError(f"Failed to load {symbol} from {path}: {e}")

    def _build_timeline(self):
        """
        Creates a master timeline by finding the UNION of all timestamps 
        across all loaded symbols.
        """
        if not self.data_store:
            self.timeline = []
            return

        # 1. Collect unique timestamps from every symbol
        all_timestamps = set()
        for df in self.data_store.values():
            if "datetime" not in df.columns:
                continue
            
            # We use unique() to avoid duplicates within one file
            ts = df["datetime"].unique().to_list()
            all_timestamps.update(ts)

        # 2. Sort them to create a linear time axis
        self.timeline = sorted(list(all_timestamps))
        
        if not self.timeline:
            print("Warning: No timestamps found in loaded data.")
            self.continue_backtest = False

    def update_bars(self) -> bool:
        """
        Advances the 'Clock' to the next timestamp.
        Returns False if end of data is reached.
        """
        if self.time_idx >= len(self.timeline):
            self.continue_backtest = False
            return False

        # 1. Update Time
        self.current_time = self.timeline[self.time_idx]
        
        # 2. Clear previous slice
        self.current_data_slice = {}

        # 3. Update 'Current Data' for this specific moment
        # Note: This is a filter operation. For massive datasets, we might optimize 
        # this with iterators later, but Polars filter is fast enough for now.
        for symbol, df in self.data_store.items():
            # Check if this symbol has data at this specific time
            # We presume the data is sorted.
            
            # Fast filter: Get rows where datetime matches current clock
            slice_df = df.filter(pl.col("datetime") == self.current_time)
            
            if not slice_df.is_empty():
                self.current_data_slice[symbol] = slice_df

        self.time_idx += 1
        return True

    def get_latest_bar(self, symbol: str) -> Optional[pl.DataFrame]:
        """
        Returns the dataframe slice for the given symbol at the CURRENT time.
        Returns None if the symbol has no data for this specific timestamp.
        """
        return self.current_data_slice.get(symbol)
    
    def get_current_time(self) -> Optional[datetime]:
        return self.current_time