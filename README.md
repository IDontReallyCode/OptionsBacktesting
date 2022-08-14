# Option trading back tester

This is my attempt to build a backtesting framework that deals with options.

_Disclaimer: I never learned to code in Python. Rather, I figure out a way. Don't point at a mistake unless you are willing to fix it ;)_




## The outline is this:

- Get the entire dataset you need for one or more tickers, including the option chains, at some specific time interval. It can be daily, 1 min, 10 min, etc.
- Initialize the `OneTicker` classes with the datasets
  - To simplify "MY" life, I will start by dealing with the data format that comes out of the TDA API
- Once all `OneTicker` have been initialized, initialize the `Market` class
- Initialize the `Account` with a deposit, a margin type, ?
- Ititialize the `Dealer` with the `Market` data
- Create your own `MyStrategy` class based on `optionbacktesting.abstractstrategy.Strategy`
- Initialize your `MyStrategy`
- Initialize `Chronos`, the god of time, with `Market`, the `Account`, the `Dealer`, the `MyStrategy`



### You are now ready to start.

The first step consist in deciding where in time do you want to start trading, because, usually, the strategy needs some data to estimate a model, or what ever. (It depends on the strategy.) You then tell chronos to "prime" the strategy.
    Priming the strategy will feed the initial set of data the strategy can use.
    The strategy is then applied and a signal "may" be generated.

The second step is to execute. Chronos has a DataFrame with a `['datetime']` column. Chronos will simply go through each entry in that column.

Executing means:

#### LOOP:
1. Tell the `Market` to move one step in time by passing the next `['datetime']`
   - This way, when the `Strategy` accesses data, it will have access to all the data "up until, and including, that date", and asking for an option chain snapshot will give the latest OC snapshot available. One can also ask for the the whole history. Same for the stock. 
2. Tell the `Dealer` execute orders.
   - The `Dealer` has a list of waiting `Order`s.
   - The `Dealer` loops through all waiting orders and tries to execute them.
     - The `Dealer` will play the role of the clients broker here and verify that the account can execute the order
       - So, it will check that there is enough capital and  get the margin [TODO]
     - If an `Order` is executed, it is removed from the queue, and a `Trade` is created
     - If and `Order` is canceled because of lack of capital or margin, a feedback is sent to the strategy [TODO]
3. Tell the `Account` to update based on the `Trade`s 
   - `Trade` shohuld also include the Margin change
   - If the `Account` requires contiunuous update, the value of each position is updated and the total value in the account is updated. [TODO]
   - The margin also needs to be recalculated based on the underlying price.
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

["date_eod", "datetime", "optionsymbol", "ticker", "pcflag", "k", "dte", "expirationdate", "bid", "ask", "bid_size", "ask_size", "openinterest", "volume"]

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

# TODO
- Category :: Priority :: Description
- Dealer :: low :: Deal with exercise of options at maturity
- Account :: high :: estimate the margin on a short single option
- Account :: med :: recognize the margin on known spreads, like verticals
- ~~Account :: med :: update the capital and the position values at each time steps to be able to assess the strategy standard deviation.~~
- Order :: med :: GTC and DAY contingent orders
- Dealer :: med :: Provide feedback on canceled orders
- Dealer :: med :: Provide flexibility on how trades are executed (bid-ask and OHLC)
- Account :: med :: Look at how the marked price is determined.

