import pytest
import polars as pl
import os
from src.data.handler import HistoricPolarsDataHandler

# --- 1. The Setup (Fixture) ---
@pytest.fixture
def mock_csv_data(tmp_path):
    """
    Creates a tiny temporary CSV file for testing.
    Returns the path to that file.
    """
    # Create a dummy dataframe with 3 timestamps
    df = pl.DataFrame({
        "datetime": [
            "2023-01-01 09:30:00", 
            "2023-01-01 09:31:00", 
            "2023-01-02 09:30:00"
        ],
        "symbol": ["SPY", "SPY", "SPY"],
        "price": [100.0, 100.5, 101.0]
    })
    
    # Save it to a temp folder managed by pytest
    file_path = tmp_path / "test_spy.csv"
    df.write_csv(file_path)
    
    return str(file_path)

# --- 2. The Unit Tests ---

def test_loading_and_caching(mock_csv_data):
    """
    Does it load the CSV and create the .arrow cache file?
    """
    config = {"SPY": mock_csv_data}
    
    # Initialize Handler
    handler = HistoricPolarsDataHandler(config)
    
    # 1. Check if data loaded into memory
    assert "SPY" in handler.data_store
    assert handler.data_store["SPY"].height == 3
    
    # 2. Check if the .arrow file was created (The caching logic)
    expected_arrow_path = mock_csv_data.replace(".csv", ".arrow")
    assert os.path.exists(expected_arrow_path)

def test_iteration_logic(mock_csv_data):
    """
    Does update_bars() correctly step through time?
    """
    config = {"SPY": mock_csv_data}
    handler = HistoricPolarsDataHandler(config)
    
    # Step 1: 09:30:00
    has_data = handler.update_bars()
    assert has_data is True
    assert "09:30:00" in str(handler.get_current_time())
    
    # Step 2: 09:31:00
    handler.update_bars()
    assert "09:31:00" in str(handler.get_current_time())
    
    # Step 3: Next Day
    handler.update_bars()
    assert "02 09:30:00" in str(handler.get_current_time())
    
    # Step 4: End of Data
    has_more = handler.update_bars()
    assert has_more is False # Should be False because we ran out of rows
    assert handler.continue_backtest is False

def test_get_latest_bar(mock_csv_data):
    """
    Does get_latest_bar return the correct slice?
    """
    config = {"SPY": mock_csv_data}
    handler = HistoricPolarsDataHandler(config)
    
    handler.update_bars() # Move to first tick
    
    bar = handler.get_latest_bar("SPY")
    
    # In our mock data, first price is 100.0
    # Polars returns a dataframe, so we extract the value
    # Option A: Get the column as a Series first (Recommended)
    price = bar["price"].item(0)

    # OR

    # # Option B: Use 2D coordinates on the DataFrame
    # price = bar.select("price").item(0, 0)
    assert price == 100.0