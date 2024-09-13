"""
    This is a basic example:

    Strategy:
        Buy as many shares of 1 stock day 1. hold.
"""

import pandas as pd
import optionbacktesting as obt
import matplotlib.pyplot as plt
import matplotlib.axes as axes


# The first thing to do is to define a strategy that inherits from the abstractstrategy.Strategy class
class MyStrategy(obt.abstractstrategy.Strategy):
    # Make sure to call the super().__init__() method
    def __init__(self) -> None:
        super().__init__()
        self.holdingnow = False

    # The main method to implement is the estimatestrategy method
    def estimatestrategy(self, marketfeedback, accountfeedback):
        # Make sure to call the super().estimatestrategy() method
        super().estimatestrategy(marketfeedback, accountfeedback)

        # The strategy we want here is to buy 1 share of the stock IF we don't already have a position
        # We will check if we have a position by looking at the account.positions.mypositions dictionary
        holdings = self.account.positions.getstockquantityforticker(ticker=self.marketdata.tickernames[0])
        if holdings>0:
            # We already have share(s), we are holding them
            self.holdingnow = True

        if not self.holdingnow:
            # We don't have a position, we will buy as much as we can with the capital
            # Check how much capital we have
            howmuch = self.account.capital
            # get the current candle for the first and only ticker
            currentcandle = self.marketdata.tickerlist[0].getcurrentstockcandle()
            # samecandle = self.marketdata.ABCDEFG.getcurrentstockcandle()
            # how many shares can we buy?
            # we will buy at the high of the current candle
            # we will buy as many shares as we can, it needs to be an integer
            howmany = int(howmuch/currentcandle.iloc[0]['high'])
            # and now we create the order
            # this time, we use a limit order
            myorder = obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=obt.ASSET_TYPE_STOCK,
                                symbol=self.marketdata.tickernames[0], action=obt.BUY_TO_OPEN, quantity=howmany, ordertype=obt.ORDER_TYPE_LIMIT,
                                triggerprice=currentcandle.iloc[0]['high'])
            self.outgoingorders.append(myorder)
        
        return self.outgoingorders
        
        

def main():
    # Get the data in a pd.DataFrame
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata['datetime'] = pd.to_datetime(stockdata['date_eod'])
    # Extract unique time steps
    uniquedaydates = pd.DataFrame(stockdata['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    # initialize the objects for the back testr
    myaccount = [obt.Account(deposit=1000)]
    tickerABCDEFG = obt.OneTicker(tickername='ABCDEFG', tickertimeseries=stockdata, optionchaintimeseries=pd.DataFrame())
    mymarket = obt.Market([tickerABCDEFG],['ABCDEFG'])
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = [MyStrategy()]
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccount, clientstrategies=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(0)

    mychronos.execute()

    print(myaccount[0].positions.mypositions)
    plt.plot(uniquedaydates, myaccount[0].totalvaluests)
    plt.show()



    pausehere=1




if __name__ == '__main__':
    main()
