"""
    This is a basic example:

    Strategy:
        Buy as many shares of 1 stock day 1. hold.
"""

import pandas as pd
import optionbacktesting as obt
import matplotlib.pyplot as plt

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
            self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=obt.ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=obt.BUY_TO_OPEN, quantity=howmany, ordertype=obt.ORDER_TYPE_LIMIT,
                                    triggerprice=samecandle.iloc[0]['high']))
        
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
