# Option trading back tester

This is my attempt to build a backtesting framework that deals with options.

_Disclaimer: I never learned to code in Python. Rather, I figure out a way. Don't point at a mistake unless you are willing to fix it ;)_


## The outline is this:

- Get the entire dataset you need for one or more tickers, including the option chains, at some specific time interval. It can be daily, 1 min, 10 min, etc.
- Initialize the oneticker classes with the datasets
  - To simplify "MY" life, I will start by dealing with the data format that comes out of the TDA API
- Once all oneticker have been initialized, initialize the market class
- Initialize the account with a deposit, a margin type, ?
- Ititialize the broker/dealer with the marketdata
- Initialize the strategy with nothing yet
- Initialize chronos, the god of time, with marketdata, the account, the broker/dealer, the strategy



### You are now ready to start.

The first step consist in deciding where in time do you want to start trading, because, usually, the strategy needs some data to estimate a model, or what ever. (It depends on the strategy.) You then tell chronos to "prime" the strategy.
    Priming the strategy will feed the initial set of data the strategy can use.
    The strategy is then applied and a signal "may" be generated.

The second step is to execute
Executing means:
#### LOOP:
1. Tell the market to move one step in time 
   - => this returns the new candle.
2. Tell the dealer to move one step in time, sends the new orders, if any, to update the list orders waiting. Also tell the dealer to try to execute the orders.
   - => this updates the order queue and the list or orders executed
   - => return the updated order queue
3. Tell the account to update based on the order updates
   - => return the new capital available
4. Update the strategy with the new candle, tell the strategy to update, 
   - => return new orders, if any.


# Appendix

## Data

### Stock price data

[for now] I assume the historical data for stocks will be of the form Open/High/Low/Close with a certain frequency (daily or x-minute data).

The DataFrame "MUST" be fed with these columns

["date_eod", "datetime", "open", "high", "low", "close", "volume"]



### Option chains data

[for now] I  assume the historical data for options was collected from snapshots and has bid/ask data with a certian frequency.

The dataFrame "MUST" be fed with these columns

["date_eod", "datetime", "ticker", "pcflag", "k", "dte", "expirationdate", "bid", "ask", "bid_size", "ask_size", "openinterest", "volume"]

#### *IMPORTANT*
Data should be sorted by pcflag, k, dte


### All DataFrame

'datetime' column needs to be of datetime format

Other columns can be there if you need them for strategy.


### Extra Data
You can send a list of extradata with their name when creating the market object.
Suppose you want to use tweets
mymarket = OptionBackTesting.Market( {...}, {...}, [tweetDataFrame], ['alltweets'])
The data will then by easily accessible inside the Strategy object by doing self.marketdata.alltweets
The only thing is that the user will be responsible for accessign only the data available so far and not access tweets which are in the future.


## Orders
[FOR NOW AT LEAST]

An order will be:
- tickerindex: int
- asset type: {stock=0, option=1}
- action: {BUY to open, SELL to close, SELL to close(all), SELL to open, BUY to close, BUY to close(all) }
- quantity: int
- type: {market=0, limit=1, stop=2}
- triggerprice: float
- k: float
- expirationdate: str/date format


## Positions
[FOR NOW AT LEAST]

A position is defined by:
- ticker: str
- asset type: {stock=0, option=1}
- quantity: int {+ for long, - for short}
- k: float
- expirationdate: str/date format


## Trades
[FOR NOW AT LEAST]

When trading options where the data has bid/ask, we always assuming the worse case scenario and BUY at ask, SELL at bid

When trading stock where the data is OHLC, we trade at Open (of following candle)

