# src/data/handler.py
**Class DataHandler(file_map: Dict[str, str])**

* `attr: continue_backtest` (bool), `attr: current_time` (Optional[datetime])
* `update_bars() -> bool`: Advances clock to next timestamp; returns False if data ends.
* `get_latest_bar(symbol: str) -> Optional[pl.DataFrame]`: Returns data slice for symbol at current timestamp.
* `get_current_time() -> Optional[datetime]`: Returns current simulation time.

# src/data/loader.py
**Class DataSourceConfig(name: str, col_map: Dict, val_map: Dict={}, date_fmt: Optional[str]=None)**

* `attr: name`, `attr: col_map`, `attr: val_map`, `attr: date_fmt`

**Presets**

* `CBOE_CONFIG`, `OPTION_METRICS_CONFIG`, `SCHWAB_CONFIG` (Instances of `DataSourceConfig`)

**Functions**

* `load_and_standardize(symbol: str, file_path: str, config: Union[DataSourceConfig, dict], output_dir: str=None, force_reload: bool=False) -> tuple[pl.DataFrame, dict]`: Ingests CSV, normalizes columns/values, optimizes memory types, caches to Arrow, returns (DataFrame, metadata).

# src/execution/broker.py
**Class Broker(data_handler)**

* `attr: data_handler`
* `execute_order(order: OrderEvent) -> Optional[FillEvent]`: Simulates execution (slippage/commission) based on current data, returns FillEvent or None.

# src/execution/exchange.py
**Class OptionExchange(data_handler)**

* `attr: data_handler`
* `check_expiration(portfolio) -> List[FillEvent]`: Scans portfolio for options expiring today; returns Fills for auto-exercise (ITM) or expiration (OTM).

# src/portfolio/portfolio.py
**Class Portfolio(initial_capital: float = 100000.0)**

* `attr: initial_capital`, `attr: current_cash`, `attr: equity`, `attr: positions` (Dict[str, Position])
* `add_cash(amount: float)`: Increases current cash balance.
* `get_position(symbol: str) -> Optional[Position]`: Retrieves a position by symbol.
* `mark_to_market(current_time, data_handler)`: Updates equity and position values using latest data.
* `add_position(symbol: str, quantity: float, price: float, commission: float=0.0, meta: Dict=None)`: Adds/updates trade, handles Options vs Stock, deducts cost & commission.

# src/portfolio/position.py
**Class Position(symbol: str, quantity: float, avg_price: float)**

* `attr: symbol`, `attr: quantity`, `attr: avg_price`, `attr: current_price`, `attr: market_value`, `attr: unrealized_pnl`, `attr: realized_pnl`
* `update_market_value(price: float)`: Updates market value and unrealized PnL based on new price.
* `close_portion(quantity: float, price: float) -> float`: Reduces quantity, updates realized PnL, returns trade PnL.

**Class OptionPosition(Position)**

* `attr: strike` (float), `attr: expiry` (Optional[date]), `attr: option_type` (Literal["C", "P"]), `attr: multiplier` (int), `attr: delta`, `attr: gamma`, `attr: theta`, `attr: vega`
* `update_market_value(price: float)`: Updates value applying the multiplier (standard 100).
* `is_itm(underlying_price: float) -> bool`: Returns True if option is In-The-Money.
* `days_to_expiry(current_date: datetime) -> int`: Returns days remaining until expiration.

# src/strategy/base.py
**Class Strategy(data_handler, portfolio)**

* `attr: data_handler`, `attr: portfolio`
* `on_bar(current_time: datetime) -> List[SignalEvent]`: Abstract main loop; returns list of actions to take.

# src/engine.py
**Class BacktestEngine(data_handler, portfolio, strategy, broker, exchange)**

* `attr: data_handler`, `attr: portfolio`, `attr: strategy`, `attr: broker`, `attr: exchange`, `attr: history` (List[Dict])
* `run() -> None`: Main Event Loop; iterates through data, handles expirations, updates portfolio, executes strategy signals.

# src/events.py
**Class Event**

* `pass` (Base class)

**Class MarketEvent(Event)**

* `attr: time` (datetime)

**Class SignalEvent(Event)**

* `attr: symbol`, `datetime`, `signal_type` ("LONG", "SHORT", "EXIT"), `strength` (float=1.0), `meta` (Optional[Dict])

**Class OrderEvent(Event)**

* `attr: symbol`, `quantity`, `order_type` ("MARKET"), `price` (Optional[float]), `meta` (Optional[Dict])

**Class FillEvent(Event)**

* `attr: datetime`, `symbol`, `quantity`, `fill_price`, `commission`, `exchange`, `meta` (Optional[Dict])