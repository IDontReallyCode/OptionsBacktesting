# Working example code snippets

## Loading stock data
```python
# =============================================================================
# 2. DATA LOADING LOGIC
# =============================================================================

def get_stock_data():
    """
    Orchestrates the data loading. 
    Now relies on loader.py to handle the Cache (Fast Path) vs Processing (Slow Path).
    """
    
    # 1. Create the Config Object
    # This defines how to map 'date_eod' -> 'datetime', etc.
    config = DataSourceConfig(
        name="StockLoader",
        col_map=COLUMN_MAPPING
    )

    # 2. Call the Loader
    # It now returns a tuple: (DataFrame, Metadata_Dict)
    # The loader itself checks if the Arrow file exists.
    try:
        df, metadata = load_and_standardize(
            symbol=TICKER_SYMBOL, 
            file_path=RAW_SOURCE_PATH, 
            config=config, 
            output_dir=PROCESSED_DIR
        )
    except Exception as e:
        # Wrap loader errors with a helpful message
        raise RuntimeError(f"Loader failed to get data for {TICKER_SYMBOL}.\nDetails: {e}")

    # 3. Display Metadata (The "Flag" you asked for)
    print(f"\n[INFO] Data Operation Complete.")
    print(f"       Source: {metadata['source'].upper()}")  # 'CACHE' or 'RAW'
    print(f"       Loaded: {metadata['path']}")
    
    return df
```

## Loading option data
```python
# =============================================================================
# 2. DATA LOADING LOGIC
# =============================================================================

def get_option_data():
    config = DataSourceConfig(
        name="OptionLoader",
        col_map=COLUMN_MAPPING,
        val_map=VALUE_MAPPING
    )

    try:
        df, metadata = load_and_standardize(
            symbol=TICKER_SYMBOL, 
            file_path=RAW_SOURCE_PATH, 
            config=config, 
            output_dir=PROCESSED_DIR
        )
    except Exception as e:
        raise RuntimeError(f"Loader failed.\nDetails: {e}")

    print(f"\n[INFO] Data Operation Complete.")
    print(f"       Source: {metadata['source'].upper()}")
    print(f"       Loaded: {metadata['path']}")
    
    return df
```

# TASK
I want a program that will load the stock data, load the option data, these are seperate in the context of optionsbacktesting project.
Then, pick a simple way to display something in times series. Example, the stock price, and the average ATM 30dte IV. 

<constraints>
- The time series will not be of the same length. We need to allow that. It is normal to train a model with more stock data than option data. For example, we might use a 100 day moving average on the stock as a signal. We need 100 more days of stock. But the display in the plot should, obviously, be synched.
</constraints>

# OUTPUT
Get me the complete python code for this example named 04_load_display_stock_option.py

## additionally
- Make sure the code is well documented for an external user looking at this example to learn about how to use this package

<!-- Did not work as the code provided was using columns not present in the dataframe -->
