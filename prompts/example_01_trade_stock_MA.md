I put my examples in subfolder

Let's not go for: 01_stock_trade_MA_Xover.py

# Description
- Loads the stock data
- Calculates the trailing moving averages and adds the columns
- Then uses the optionsbacktesting infrastructure and the strategy is to buy-sell on 2 moving averages cross-over
    - The MA lenghts are variables easy to change
    - We do go not allow going short if we do not have the stock

# Instructions
- For this to work, I believe we need to create a "strategy.py" file in the src/strategy/ folder.
- We may also need an "example.py" file to load the data and prepare the dataframe. If we go that route, can we pick a different name for the "cached" version of the data?
- For now, do not work on the code, instead, act as "staff" and analyse what I am asking for here, and improve it if need be
