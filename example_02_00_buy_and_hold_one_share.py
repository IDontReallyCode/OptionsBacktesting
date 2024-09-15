"""
    This is a basic example:

    Strategy:
        Buy the stock day 1. hold.
"""

# import numpy as np
import pandas as pd
import optionbacktesting as obt
# import datetime
import matplotlib.pyplot as plt
import matplotlib.axes as axes

from optionbacktesting.broker import ASSET_TYPE_STOCK, BUY_TO_OPEN

# The first thing to do is to define a strategy that inherits from the abstractstrategy.Strategy class
class MyStrategy(obt.abstractstrategy.Strategy):
    # Make sure to call the super().__init__() method
    def __init__(self) -> None:
        super().__init__()
        self.holdingnow = False

    # The main method to implement is the estimatestrategy method
    def estimatestrategy(self, marketfeedback, accountfeedback)->list[obt.broker.Order]:
        # Make sure to call the super().estimatestrategy() method
        super().estimatestrategy(marketfeedback, accountfeedback)

        # The strategy we want here is to buy 1 share of the stock IF we don't already have a position
        # We will check if we have a position by looking at the account.positions.mypositions dictionary
        holdings = self.account.positions.getstockquantityforticker(ticker=self.marketdata.tickernames[0])
        if holdings>0:
            # We already have a share, we are holding the stock
            self.holdingnow = True

        if not self.holdingnow:
            # We don't have a position, we will buy 1 share
            # To do this, we will create an Order object and append it to the self.outgoingorders list
            myorder = obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1)
            self.outgoingorders.append(myorder)
        
        return self.outgoingorders
        
        

def main():
    """
        Get data into a pd.Dataframe
        Make sure it has the required columns        
    """
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata['datetime'] = pd.to_datetime(stockdata['date_eod'])
    """
        Extract the unique time steps that will be passed to Chronos
    """
    uniquedaydates = pd.DataFrame(stockdata['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    """
        Initialize the objects we need to run the strategy back tester
    """
    # First, we need to create an Account object to hold the positions and the cash
    # We will initialize the account with 1000 USD
    myaccount = [obt.Account(deposit=1000)]
    # We need to create a Market object to hold the data
    # We will create a OneTicker object to hold the stock data for one ticker. We can create multiple OneTicker objects if we have multiple tickers
    tickerRANDOM = obt.OneTicker(tickername='RANDOM', tickertimeseries=stockdata, optionchaintimeseries=pd.DataFrame())
    # We will create a Market object to hold the OneTicker objects
    mymarket = obt.Market([tickerRANDOM],['RANDOM'])
    # We need to create a Dealer object to handle the orders
    # We will initialize the dealer with the marketdata, but there are other parameters that we could set.
    mydealer = obt.Dealer(marketdata=mymarket)
    # We need to create a Strategy list to hold the list of all strategies. (Only one strategy here)
    mystrategy = [MyStrategy()]                         # Needs to be a list
    # Finally, we need to create a Chronos object to run the back test
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccount, clientstrategies=mystrategy, chronology=uniquedaydates)

    # Tell Chronos were you want to start testing the strategy in the time series of unique time steps by sending the index
    mychronos.primingthestrategyat(0)

    # Run the back test
    mychronos.execute()

    # Plot the results
    ax1: axes._axes.Axes
    ax2: axes._axes.Axes
    print(myaccount[0].positions.mypositions)
    fig, (ax1, ax2) = plt.subplots(2,1, sharex=True, sharey=False)
    ax1.plot(uniquedaydates, myaccount[0].totalvaluests)
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates, myaccount[0].positionvaluests)
    ax2.plot(uniquedaydates, stockdata['close'])
    ax2.set_title('position value VS stock price \n(position value is updated after the fact. \nthis is why it is lagged)')
    fig.tight_layout()
    plt.show()

    print('all orders submitted')
    print(pd.DataFrame(mydealer.orderlistall))
    # [TODO] have the action print as BUY or SELL instead of 1 or -1

    print('\nall orders executed')
    print(pd.DataFrame(mydealer.orderlistexecuted))

    pausehere=1




if __name__ == '__main__':
    main()
