This is my attempt to build a backtesting framework that deals with options

The outline is this:

1- Get the entire dataset you need for one or more tickers, including the option chains, at some specific time interval. It can be daily, 1 min, 10 min, etc.

2- Initialize the oneticker classes with the datasets

  2.1- To simplify "MY" life, I will start by dealing with the data format that comes out of the TDA API
  
3- Once all oneticker have been initialized, initialize the market class

4- Initialize the account with a deposit, a margin type, ?

5- Ititialize the broker/dealer with the marketdata

6- Initialize the strategy with nothing yet

7- Initialize chronos, the god of time, with marketdata, the account, the broker/dealer, the strategy



You are now ready to start.

The first step consist in deciding where in time do you want to start trading, because, usually, the strategy needs some data to estimate a model, or what ever. (It depends on the strategy.) You then tell chronos to "prime" the strategy.
    Priming the strategy will feed the initial set of data the strategy can use.
    The strategy is then applied and a signal "may" be generated.

The second step is to execute
  Executing means:
    LOOP:
      1- Tell the market to move one step in time 
        => this returns the new candle.
      2- Tell the dealer to move one step in time, sends the new orders, if any, to update the list orders waiting. Also tell the dealer to try to execute the orders.
        => this updates the order queue and the list or orders executed
        => return the updated order queue
      3- Tell the account to update based on the order updates
        => return the new capital available
      4- Update the strategy with the new candle, tell the strategy to update, 
        => return new orders, if any.


