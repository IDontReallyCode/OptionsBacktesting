# src/data/handler.py
**Class DataHandler(file_map: Dict[str, str])**

* `attr: continue_backtest` (bool), `attr: current_time` (Optional[datetime])
* `update_bars() -> bool`: Advances clock to next timestamp; returns False if data ends.
* `get_latest_bar(symbol: str) -> Optional[pl.DataFrame]`: Returns data slice for symbol at current timestamp.
* `get_current_time() -> Optional[datetime]`: Returns current simulation time.

