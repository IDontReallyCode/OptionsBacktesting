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

from optionbacktesting.broker import ASSET_TYPE_STOCK, BUY_TO_OPEN, ORDER_TYPE_LIMIT


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
            currentcandle = self.marketdata.tickerlist[0].getcurrentstockcandle()
            samecandle = self.marketdata.ABCDEFG.getcurrentstockcandle()
            howmuch = self.account.capital
            howmany = int(howmuch/samecandle.iloc[0]['high'])
            self.outgoingorders.append(obt.Order(tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=howmany, ordertype=ORDER_TYPE_LIMIT,
                                    triggerprice=samecandle.iloc[0]['high']))
        
        return self.outgoingorders
        
        

def main():
    myaccount = obt.Account(deposit=1000)
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata['datetime'] = pd.to_datetime(stockdata['date_eod'])
    uniquedaydates = pd.DataFrame(stockdata['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    tickerABCDEFG = obt.OneTicker(tickername='ABCDEFG', tickertimeseries=stockdata, optionchaintimeseries=pd.DataFrame())
    
    mymarket = obt.Market([tickerABCDEFG],['ABCDEFG'])
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(0)

    mychronos.execute()

    print(myaccount.positions.mypositions)
    plt.plot(uniquedaydates, myaccount.totalvaluests)
    plt.show()
    # plt.plot(uniquedaydates, myaccount.positionvaluests)
    # plt.plot(uniquedaydates, stockdata['close'])
    # plt.show()
    pausehere=1




if __name__ == '__main__':
    main()
