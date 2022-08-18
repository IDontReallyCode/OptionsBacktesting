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
            self.outgoingorders.append(obt.Order(tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1))
        
        return self.outgoingorders
        
        

def main():
    myaccount = obt.Account(deposit=1000)
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata['datetime'] = pd.to_datetime(stockdata['date_eod'])
    uniquedaydates = pd.DataFrame(stockdata['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    tickerRANDOM = obt.OneTicker(tickername='RANDOM', tickertimeseries=stockdata, optionchaintimeseries=pd.DataFrame())
    
    mymarket = obt.Market([tickerRANDOM],['RANDOM'])
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(0)

    mychronos.execute()

    print(myaccount.positions.mypositions)
    fig, (ax1, ax2) = plt.subplots(2,1, sharex=True, sharey=False)
    ax1.plot(uniquedaydates, myaccount.totalvaluests)
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates, myaccount.positionvaluests)
    ax2.plot(uniquedaydates, stockdata['close'])
    ax2.set_title('position value VS stock price \n(position value is updated after the fact. \nthis is why it is lagged)')
    fig.tight_layout()
    plt.show()
    pausehere=1




if __name__ == '__main__':
    main()
