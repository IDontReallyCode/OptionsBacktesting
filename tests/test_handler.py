import pytest
import polars as pl
from datetime import datetime, timedelta
from src.data.handler import DataHandler

@pytest.fixture
def mock_arrow_files(tmp_path):
    """
    Creates two temporary .arrow files with overlapping timelines.
    Stock: T1, T2, T3
    Option: T2, T3, T4
    Expected Union: T1, T2, T3, T4
    """
    base_time = datetime(2023, 1, 1, 9, 30)
    times = [base_time + timedelta(minutes=i) for i in range(5)]
    
    # 1. Stock Data (Times 0, 1, 2)
    df_stock = pl.DataFrame({
        "datetime": [times[0], times[1], times[2]],
        "symbol": ["SPY", "SPY", "SPY"],
        "price": [100.0, 101.0, 102.0]
    })
    path_stock = tmp_path / "spy_stock.arrow"
    df_stock.write_ipc(path_stock)
    
    # 2. Option Data (Times 1, 2, 3) - Overlaps at T1, T2; Unique at T3
    df_opt = pl.DataFrame({
        "datetime": [times[1], times[2], times[3]],
        "symbol": ["SPY_OPT", "SPY_OPT", "SPY_OPT"],
        "strike": [100, 100, 100]
    })
    path_opt = tmp_path / "spy_opt.arrow"
    df_opt.write_ipc(path_opt)
    
    return {
        "SPY": str(path_stock),
        "SPY_OPT": str(path_opt)
    }, times

def test_handler_synchronization(mock_arrow_files):
    file_map, times = mock_arrow_files
    handler = DataHandler(file_map)
    
    # 1. Check Timeline Construction
    # Should have 4 unique steps: T0, T1, T2, T3
    assert len(handler.timeline) == 4
    assert handler.timeline[0] == times[0]
    assert handler.timeline[-1] == times[3]
    
    # 2. Step 1: T0 (Only Stock)
    assert handler.update_bars() is True
    assert handler.get_current_time() == times[0]
    assert handler.get_latest_bar("SPY") is not None
    assert handler.get_latest_bar("SPY_OPT") is None # Options didn't trade yet
    
    # 3. Step 2: T1 (Both)
    assert handler.update_bars() is True
    assert handler.get_current_time() == times[1]
    assert handler.get_latest_bar("SPY")["price"][0] == 101.0
    assert handler.get_latest_bar("SPY_OPT") is not None
    
    # 4. Step 3: T2 (Both)
    assert handler.update_bars() is True
    
    # 5. Step 4: T3 (Only Option)
    assert handler.update_bars() is True
    assert handler.get_current_time() == times[3]
    assert handler.get_latest_bar("SPY") is None # Stock stopped trading
    assert handler.get_latest_bar("SPY_OPT") is not None
    
    # 6. End of Data
    assert handler.update_bars() is False
    assert handler.continue_backtest is False