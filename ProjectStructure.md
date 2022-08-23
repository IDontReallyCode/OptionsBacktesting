# Classes Structure

- `OneTicker`  [link](./optionbacktesting/oneticker.py)
  - `pd.DataFrame` of stock times series
  - `pd.DataFrame` of option snapshots
- `Market`  [link](./optionbacktesting/market.py)
  -  `list[OneTicker]`
  -  `list[tickernames:str]`
-  Broker  [link](./optionbacktesting/broker.py)
   -  `Order`
   -  `Trade`
   -  `Positions`
   -  `Dealer`
      -  `Marker`
   -  `Account`
      -  `Positions`
-  `Strategy`  [link](./optionbacktesting/abstractstrategy.py)
   -  `Marker`
   -  `Account`
-  `Chronos`   [link](./optionbacktesting/chronos.py)
   -  `Market`
   -  `Dealer`
   -  `Account`
   -  `Strategy`
   -  `pd.DataFrame'  time series to drive the back test.


