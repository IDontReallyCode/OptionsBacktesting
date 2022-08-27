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

from optionbacktesting.broker import ASSET_TYPE_STOCK, BUY_TO_OPEN


class MyStrategy(obt.abstractstrategy.Strategy):
    def __init__(self) -> None:
        super().__init__()
        self.holdingnow = False


    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)

        holdings = self.account.positions.getstockquantityforticker(ticker=self.marketdata.tickernames[0])
        if holdings>0:
            self.holdingnow = True

        if not self.holdingnow:
            self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1))
        
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
    myaccount = [obt.Account(deposit=1000)]
    tickerRANDOM = obt.OneTicker(tickername='RANDOM', tickertimeseries=stockdata, optionchaintimeseries=pd.DataFrame())
    mymarket = obt.Market([tickerRANDOM],['RANDOM'])
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = [MyStrategy()]                         # Needs to be a list
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccount, clientstrategies=mystrategy, chronology=uniquedaydates)

    # Tell Chronos were you want to start testing the strategy in the time series of unique time steps by sending the index
    mychronos.primingthestrategyat(0)

    mychronos.execute()

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
