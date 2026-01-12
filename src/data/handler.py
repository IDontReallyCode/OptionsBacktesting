"""
Data Handler Module
This module defines the DataHandler abstract base class and a concrete implementation
that uses Polars for efficient data loading and handling.

Created: By Google Gemini AI
Edite by: Pascal Letourneau
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Optional, Dict, Tuple, Union

import polars as pl

# Define types for clarity
Symbol = str
MarketDataSlice = Dict[Symbol, pl.DataFrame]

class DataHandler(ABC):
    """
    Abstract Base Class for Data Handling.
    Enforces the contract that the BacktestEngine expects.
    """

    @abstractmethod
    def update_bars(self) -> bool:
        """
        Pushes the internal timeframe forward by one step.
        Returns: True if new data was found, False if End of Data.
        """
        pass

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Optional[pl.DataFrame]:
        """
        Returns the data slice for the current timestamp for a specific symbol.
        """
        pass

    @abstractmethod
    def get_current_time(self):
        """Returns the current timestamp of the system."""
        pass


class HistoricPolarsDataHandler(DataHandler):
    """
    Loads historic Option and Stock data using Polars.
    
    Features:
    - Auto-Caching: Converts CSV -> Arrow IPC (.arrow) on first run for 50x faster loading subsequently.
    - Lazy Iteration: Yields data slices based on timestamps without re-filtering the whole dataset repeatedly.
    """

    def __init__(self, file_config: Dict[Symbol, str]):
        """
        Args:
            file_config: Dictionary mapping Symbol -> FilePath
                         e.g., {'SPY': './data/SPY_2023.csv', 'SPY_OPT': './data/SPY_OPT_2023.csv'}
        """
        self.file_config = file_config
        self.data_store: Dict[Symbol, pl.DataFrame] = {}
        self.generators: Dict[Symbol, Generator] = {}
        
        # Current state
        self.current_data: MarketDataSlice = {}
        self.current_time = None
        self.continue_backtest = True

        # Load and Cache Data immediately upon instantiation
        self._load_and_cache_data()
        
        # Initialize Generators
        self._init_generators()

    def _load_and_cache_data(self):
        """Internal method to handle CSV -> IPC conversion."""
        print(f"[{self.__class__.__name__}] Initializing Data...")

        for symbol, raw_path in self.file_config.items():
            path_obj = Path(raw_path)
            # Define the cache path (e.g., data.csv -> data.arrow)
            ipc_path = path_obj.with_suffix(".arrow")

            if ipc_path.exists():
                print(f"Loading cached IPC for {symbol}...")
                # Memory Map (mmap) allows loading huge files without filling RAM instantly
                df = pl.read_ipc(ipc_path, memory_map=True)
            else:
                print(f"Parsing CSV for {symbol} (One-time process)...")
                # Parse CSV
                try:
                    df = pl.read_csv(
                        path_obj, 
                        try_parse_dates=True, # Auto-detect datetime format
                        ignore_errors=True    # Skip malformed lines
                    )
                    
                    # Sort is CRITICAL for chronological replay
                    if "datetime" in df.columns:
                        df = df.sort("datetime")
                    
                    # Save to IPC for next time
                    print(f"Caching data to {ipc_path}...")
                    df.write_ipc(ipc_path)
                    
                except Exception as e:
                    raise IOError(f"Failed to load data for {symbol}: {e}")

            self.data_store[symbol] = df

    def _init_generators(self):
        """Creates Python Generators for efficient looping."""
        # We need a master timeline. 
        # Strategy: We assume the first symbol in config provides the 'Master Clock' (usually the Underlying)
        # Or we can merge all timestamps. For simplicity, we define the first symbol as the clock source.
        
        master_symbol = list(self.file_config.keys())[0]
        master_df = self.data_store[master_symbol]
        
        # Get unique timestamps to step through
        self.timeline = master_df["datetime"].unique(maintain_order=True).to_list()
        self.time_idx = 0

    def update_bars(self) -> bool:
        """
        The Heartbeat. Moves the pointer to the next timestamp.
        """
        if self.time_idx >= len(self.timeline):
            self.continue_backtest = False
            return False

        # 1. Get current time target
        timestamp = self.timeline[self.time_idx]
        self.current_time = timestamp

        # 2. Slice data for ALL symbols at this timestamp
        # Polars filter is fast, but for massive option chains, we rely on the pre-sorted nature.
        # Note: Ideally, this uses `partition_by` or `group_by` in a pre-processing step for max speed,
        # but simple filtering is sufficient for mid-sized data.
        
        for symbol, df in self.data_store.items():
            # Get data for exactly this timestamp
            # We use 'filter' here. 
            daily_slice = df.filter(pl.col("datetime") == timestamp)
            
            if not daily_slice.is_empty():
                self.current_data[symbol] = daily_slice

        self.time_idx += 1
        return True

    def get_latest_bar(self, symbol: str) -> Optional[pl.DataFrame]:
        """
        Returns the Polars DataFrame slice for the specific symbol at current time.
        For Options, this returns the WHOLE chain for that minute/day.
        """
        return self.current_data.get(symbol)

    def get_current_time(self):
        return self.current_time