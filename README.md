# Option trading back tester

This is my attempt to build a backtesting framework that deals with options.

_Disclaimer: I never learned to code in Python. Rather, I figure out a way. Don't point at a mistake unless you are willing to fix it ;)_




## The outline is this:

- Get the entire dataset you need for one or more tickers, including the option chains, at some specific time interval. It can be daily, 1 min, 10 min, etc.
- Initialize the `OneTicker` classes with the datasets
  - To simplify "MY" life, I will start by dealing with a DataFrame with specific columns, see [here](#data)
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
[SOMETHING SEEMS OFF IN THE LOGIC HERE]
1. Tell the `Market` to move one step in time by passing the next `['datetime']`
   - This way, when the `Strategy` (or any other object) accesses data, it can ask for all the data "up until, and including, that datetime", or, "the lastest data", which would be the latest snapshot for options, or the latest candle for stocks. 
2. Tell the `Dealer` execute orders.
   - The `Dealer` has a list of waiting `Order`s.
   - The `Dealer` loops through all waiting orders and tries to execute them.
     - The `Dealer` will play the role of the clients' broker here and verify that the account can execute the order
       - So, it will check that there is enough capital and  get the margin [TODO]
     - If an `Order` is executed, it is removed from the queue, and a `Trade` is created
     - If and `Order` is canceled because of lack of capital or margin, a feedback is sent to the strategy [TODO]
3. Tell the `Account` to update based on the `Trade`s 
   - `Trade` should also include the Margin change.
   - The value of each position is updated and the total value in the account is updated.
   - The margin also needs to be recalculated based on the underlying price.
4. Tell the `Strategy` to update, 
   - return new orders, if any.
5. Send the new `Order`'s from `Strategy` and send them to the `Dealer`
   - This is when we check for margin impact
6. Update the `Positions` values and the total portfolio values
   - The margin amounts will be updated as well. See [here](#margins)
 


# Appendix

## Data

### Stock price data

[for now] I assume the historical data for stocks will be of the form Open/High/Low/Close with a certain frequency (daily or x-minute data).

The DataFrame "MUST" be fed with these columns

["date_eod", "datetime", "open", "high", "low", "close", "volume"]



### Option chains data

[for now] I  assume the historical data for options was collected from snapshots and has bid/ask data with a certain frequency.

The dataFrame "MUST" be fed with these columns

["date_eod", "datetime", "optionsymbol", "ticker", "pcflag", "k", "dte", "expirationdate", "bid", "ask", "bid_size", "ask_size", "openinterest", "volume"]

#### *IMPORTANT*
Data should be sorted by datetime, pcflag, k, dte 
*TODO: Verify if this is still required.


### All DataFrame
'datetime' column needs to be of datetime format

Other columns can be there if you need them for strategy.


## Extra Data
You can send a list of extradata with their name when creating the market object.
Suppose you want to use tweets

mymarket = OptionBackTesting.Market( {...}, {...}, [tweetDataFrame], ['alltweets'])

The data will then by easily accessible inside the Strategy object by doing self.marketdata.alltweets

The only thing is that the user will be responsible for accessign only the data available so far and not access tweets which are in the future.


## Orders
[FOR NOW AT LEAST]

        An order will be:
            - tickerindex: int      {the index number of the asset, makes things easier for the coding}
            - ticker: str           {Get it from Market.tickernames[tickerindex]}
            - asset type:           {ASSET_TYPE_STOCK = 0, ASSET_TYPE_OPTION = 1}
            - symbol: str           {the ticker for a stock, the unique symbol for an option}
            - action:               {BUY_TO_OPEN = 1, SELL_TO_CLOSE = -1}
            - quantity: int 
            - ordertype:            {ORDER_TYPE_MARKET = 0, ORDER_TYPE_LIMIT = 1, ORDER_TYPE_STOP = 2}
            - tickerprice: float    {Required for margin calculation when shorting options}
            - optionprice: float    {Required for margin calculation when shorting options}
            - triggerprice: float   {for contingent orders}
            - put call flag         {put=0, call=1}
            - strike k
            - expiration date


## Positions
[FOR NOW AT LEAST]

A position is defined by:
    mypositions = {'tic1': {'equity': {'symbol': 'AMD', 'quantity': 5, 'tradeprice':18.56}, 
                            'options': {'optionsymbol1': {'quantity': 5, 'pcflag': 0, 'k':10.0, 'expirationdate':'2000-01-01', 'tradeprice':5.56}, 
                                    'optionsymbol2': {'quantity': 5, 'pcflag': 0, 'k':20.0, 'expirationdate':'2000-01-01', 'tradeprice':1.56} }},
                    'tic2': {'equity':{'symbol': 'AAPL', 'quantity': 5, 'tradeprice':154.23}},
                    'tic3': {'options':{'optionsymbol1': {'quantity': 5, 'pcflag': 0, 'k':10.0, 'expirationdate':'2000-01-01', 'tradeprice':0.56}, 
                                    'optionsymbol2': {'quantity': 5, 'pcflag': 0, 'k':20.0, 'expirationdate':'2000-01-01', 'tradeprice':1.56} }}
                    }

## Trades

When trading options where the data has bid/ask, we allow for multiple types of execution between the bid-ask. Worst Case Scenario, Best Case Scenario, at 25%, 50%, or 75% of the bid-ask spread, or at a random price between the bid-ask spread.

When trading stock where the data is OHLC, we trade at Open (of following candle) [For now, at least]
[TODO] For a Market order, we can trade at different levels between the low and high. Even a random price between the two.
[TODO] For Limit/Stop order, we can allow the trade if the limit/stop is between the low-high.


## Margins
THIS IS NO LONGER UP TO DATE SINCE TD is dead
The margins would be based on Schwab reference web page: [https://www.schwab.com/margin/margin-rates-and-requirements](https://www.schwab.com/margin/margin-rates-and-requirements)


~~Margin calculations are quite tricky and dependent on multiple factors.~~

~~So here is what I settle for, for now:~~
~~- Margin requirements will be calculated following the TDA guide above.~~
~~- For now, I will calculate each position independently.~~
~~- In the future, I could expand the code to allow trading spreads directly and calculate spread margins.~~
~~- The user of the back testing framework is free to consider the margin or not.~~

~~However, for now, we take the following approach:~~
~~- Make a deposit in the `Account` when you initialize it at a level that "makes sense" based on the strategy you back test.~~
~~- The `Account` value will be updated at each time step on the `chronology` time series passed to `Chronos`.~~
~~- To assess the performance on the strategy, inspect the time series of the `Account` values.~~

~~Calculating the Margins is set aside for now. Reasons include:~~
~~- When calculating the margin requirement for options, the formula depends on the type of spread, how the spread was calculated, and the broker.~~
~~- For example,~~ ~~
~~- with TDA, when shorting a straddle, the margin requirement = MAX( call margin, put margin )~~
~~- (I was told, but did not verify) that with IB, the margin was the call margin.~~
~~- When legging into the short straddle, instead of trading a short straddle, apparently (I have not verified) with TDA, the margin would be "grossed out", i.e., the spread would be "detected", and only the MAX( call margin, put margin ) would be required. However, (I was told but did not verify) that with IB, that would not be the case, i.e., both margins would be required.~~
~~- If the end goal is to assess the performance of a strategy, perhaps it is better to give it a certain allocation, and see how the account value changes based on the strategy, and not bother too much with the margin requirements.~~
~~- Because of all this, I decide to put margin calculation aside for now.~~



# TODO
- [ ] Category :: Priority :: Description
- [ ] Dealer :: low :: Deal with exercise of options at maturity
- [x] Account :: high :: estimate the margin on a short single option
- [ ] Account :: med :: recognize the margin on known spreads, like verticals
- [x] Account :: med :: update the capital and the position values at each time steps to be able to assess the strategy standard deviation.
- [ ] Order :: med :: GTC and DAY contingent orders
- [ ] Dealer :: med :: Provide feedback on canceled orders
- [ ] Dealer :: med :: Provide flexibility on how trades are executed (bid-ask and OHLC) Done for options
- [ ] Account :: med :: Look at how the marked price is determined.
- [ ] Chronos :: high :: make strategies and matching accounts in lists so we can treat multiple strategies at once
- [ ] Strategy :: low :: Provide some basic strategies that the user can add automatically, like buy-and-hold for ticker [0]
- [ ] Account :: med :: automate the tracking of ticker positions
