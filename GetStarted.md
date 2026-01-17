# Guide: Backtesting a New Option Strategy

## Overview
To backtest a new ticker and strategy, you must move through three distinct layers of your architecture:
1.  **Data Layer**: Ingest raw CSVs and convert them into the system's optimized `.arrow` format.
2.  **Logic Layer**: Write the specific trading rules in a new Strategy class.
3.  **Execution Layer**: Wire the components together in a run script to start the Event Loop.

---

## Phase 1: Data Preparation (The Loader)
*Before the engine can run, it needs fast, standardized data. Your `DataHandler` cannot read raw CSVs directly; it requires pre-processed Arrow files.*

### 1. Acquire Raw Data
Obtain the historical text files for your new ticker (e.g., `NVDA`). You need two distinct datasets:
* **Stock History:** Timestamp, Open, High, Low, Close, Volume.
* **Option Chain History:** A massive file containing every quote for every strike and expiration for every minute (or day) of the backtest period.

### 2. Define the Data Source Configuration
Check if your data provider matches an existing preset in `src/data/loader.py` (e.g., `CBOE_CONFIG`, `SCHWAB_CONFIG`).
* **If yes:** You are ready to load.
* **If no:** You must define a new `DataSourceConfig`. This maps the "messy" column names in your CSV (e.g., `PutCallFlag`) to the internal system names (`option_type`) and standardizes values (e.g., `0` becomes `P`).

### 3. Run the Standardization Process
Use the `load_and_standardize` function from the `loader` module.
* **Input:** Your raw CSV paths and the Config object from step 2.
* **Action:** The loader will normalize columns, optimize memory (downcasting floats/ints), and sort time indexes.
* **Output:** It will generate `.arrow` files in your data directory (e.g., `data/NVDA.arrow` and `data/NVDA_OPT.arrow`).

---

## Phase 2: Strategy Development (The Logic)
*Now that data is ready, you define **when** to trade.*

### 1. Create a New Strategy Class
Create a new file in `src/strategy/` (e.g., `nvda_iron_condor.py`). Define a class that inherits from the `Strategy` base class found in `src/strategy/base.py`.

### 2. Implement the `on_bar` Loop
You must override the `on_bar(current_time)` method. This is where your trading logic lives.
* **Access Stock Data:** Call `self.data_handler.get_latest_bar("NVDA")` to check technical indicators (RSI, SMA) or price action.
* **Access Option Chain:** Call `self.data_handler.get_latest_bar("NVDA_OPT")` to get the full option chain for that specific timestamp.

### 3. Filter the Option Chain
The chain returns *all* contracts. You must write logic to filter this DataFrame:
* **By Expiration:** Filter for dates `> current_time` (e.g., 30-45 DTE).
* **By Type:** Separate Calls and Puts.
* **By Moneyness:** Calculate the distance between the Strike and the current Underlying Price to find ITM/OTM contracts.

### 4. Generate Signals
If your entry conditions are met (e.g., "Stock RSI > 70"), construct `SignalEvent` objects.
* **Signal Content:** Specify the specific `symbol` (the option contract ID), the `signal_type` ("LONG", "SHORT", "EXIT"), and any metadata.
* **Return:** The `on_bar` method must return a *list* of these signals.

---

## Phase 3: Simulation Setup (The Engine)
*This is the "wiring" phase where you connect all independent components.*

### 1. Initialize the Data Handler
Instantiate the `DataHandler` with a **File Map**. This dictionary tells the system which internal symbol maps to which Arrow file.
* *Example:* Map `"NVDA"` to `data/NVDA.arrow` and `"NVDA_OPT"` to `data/NVDA_OPT.arrow`.

### 2. Initialize Support Components
Create instances of the core infrastructure classes:
* **Portfolio:** Set your starting capital (e.g., $100,000).
* **Broker:** Pass the `DataHandler` to it (so it can look up prices for execution).
* **Exchange:** Pass the `DataHandler` to it (so it can check settlement prices for expiration).

### 3. Initialize Your Strategy
Instantiate the class you created in Phase 2. Pass it the `DataHandler` and the `Portfolio` so it can see prices and check your current holdings.

### 4. Configure the Engine
Instantiate the `BacktestEngine`. You will pass in all the objects created above:
* `data_handler`
* `portfolio`
* `strategy`
* `broker`
* `exchange`

---

## Phase 4: Execution & Analysis
*Run the simulation.*

### 1. Run the Loop
Call the `engine.run()` method.
* The system will tick through every timestamp in your data.
* It will automatically handle option expirations (via `Exchange`).
* It will execute your signals (via `Broker`).
* It will track your PnL (via `Portfolio`).

### 2. Review Results
Once the run completes, inspect `engine.history`. This list contains the snapshots of your Equity and Cash at every timestamp, allowing you to plot an equity curve or calculate Sharpe Ratios.