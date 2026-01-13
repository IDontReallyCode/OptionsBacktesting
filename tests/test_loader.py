import pytest
import polars as pl
import os
from src.data.loader import load_and_standardize, DataSourceConfig

# Define a "Weird" Vendor Format for testing
TEST_CONFIG = DataSourceConfig(
    name="TEST_VENDOR",
    col_map={
        "t": "datetime",
        "sym": "symbol",
        "u_prc": "underlying_price",
        "k": "strike",
        "exp": "expiry",
        "b": "bid",
        "a": "ask",
        "v": "volume",       # Added mapping for volume
        "cp": "option_type"
    },
    val_map={
        "option_type": {"call": "C", "put": "P"}
    }
)

@pytest.fixture
def mock_raw_csv(tmp_path):
    """Creates a temporary messy CSV file."""
    csv_path = tmp_path / "test_data.csv"
    
    # Create data with "Weird" column names and values
    df = pl.DataFrame({
        "t": ["2023-01-01 09:30:00", "2023-01-01 09:31:00"],
        "sym": ["SPY", "SPY"],
        "u_prc": [400.0, 400.5],
        "k": [400.0, 400.0],
        "exp": ["2023-01-20", "2023-01-20"],
        "b": [10.0, 10.1],
        "a": [10.2, 10.3],
        "v": [100, 500],           # Added Volume data
        "cp": ["call", "put"]      # Mixed case/values
    })
    
    df.write_csv(csv_path)
    return str(csv_path)

def test_loader_standardization(mock_raw_csv):
    """
    Test that the loader:
    1. Renames columns correctly (t -> datetime)
    2. Maps values correctly (call -> C)
    3. Optimizes Types (Categorical, UInt32)
    4. Calculates derived cols (mid)
    5. Creates the IPC file
    """
    # 0. Setup output directory (same as input for testing)
    temp_dir = os.path.dirname(mock_raw_csv)

    # Run Loader
    # We explicitly pass output_dir so it doesn't try to write to real "data/" folder
    df = load_and_standardize("SPY", mock_raw_csv, TEST_CONFIG, output_dir=temp_dir)
    
    # 1. Check Column Names
    assert "datetime" in df.columns
    assert "strike" in df.columns
    assert "volume" in df.columns
    assert "k" not in df.columns # Should be gone/renamed
    
    # 2. Check Value Mapping
    # Row 0 was 'call', should be 'C'
    assert df["option_type"][0] == "C"
    # Row 1 was 'put', should be 'P'
    assert df["option_type"][1] == "P"

    # 3. Check Memory Optimizations (Types)
    # Option Type should be Categorical (not String)
    assert df["option_type"].dtype == pl.Categorical
    # Symbol should be Categorical
    assert df["symbol"].dtype == pl.Categorical
    # Volume should be UInt32 (efficient integer)
    assert df["volume"].dtype == pl.UInt32
    
    # 4. Check Derived Column (Midpoint)
    # Row 0: Bid 10.0, Ask 10.2 -> Mid 10.1
    assert df["mid"][0] == 10.1
    
    # 5. Check Cache Creation
    # The loader saves the file as "{SYMBOL}.arrow", regardless of input filename
    expected_arrow = os.path.join(temp_dir, "SPY.arrow")
    
    assert pl.read_ipc(expected_arrow).height == 2