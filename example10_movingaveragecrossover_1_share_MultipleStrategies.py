"""
    This is a basic example:

    Strategy:
        Buy the stock day 1. hold.
"""

import numpy as np
import pandas as pd
import optionbacktesting as obt
# import datetime
import matplotlib.pyplot as plt

from optionbacktesting.broker import ASSET_TYPE_STOCK, BUY_TO_OPEN, ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET, SELL_TO_CLOSE


class MyStrategy(obt.abstractstrategy.Strategy):
    def __init__(self, ma_size:int, short:int = 7, long:int=21) -> None:
        super().__init__()
        self.holdingnow = False
        self.ma_short_length = short
        self.ma_long__length = long
        self.movingaverageshort = np.zeros((ma_size,))
        self.movingaverage_long = np.zeros((ma_size,))
        self.movingaveragesignl = np.zeros((ma_size,))


    def priming(self, marketdata: obt.Market, account: obt.Account):
        super().priming(marketdata, account)

        historicaldata = self.marketdata.tickerlist[0].getstockdata()
        self.movingaverage_long[0] = np.average(historicaldata.iloc[-self.ma_long__length:]['close'])
        self.movingaverageshort[0] = np.average(historicaldata.iloc[-self.ma_short_length:]['close'])
        self.timer = 1

        

    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)

        lastcandle = self.marketdata.tickerlist[0].getcurrentstockcandle()
        self.movingaverage_long[self.timer] = (self.movingaverage_long[self.timer-1]*(self.ma_long__length-1) + 
                                                lastcandle.iloc[0]['close'])/(self.ma_long__length)
        self.movingaverageshort[self.timer] = (self.movingaverageshort[self.timer-1]*(self.ma_short_length-1) + 
                                                lastcandle.iloc[0]['close'])/(self.ma_short_length)
        if   self.movingaverage_long[self.timer-1] >= self.movingaverageshort[self.timer-1]: 
            if   self.movingaverage_long[self.timer] < self.movingaverageshort[self.timer]:
                # short was below long, cross over, BUY signal
                self.movingaveragesignl[self.timer]=+1
            else:
                # no crossing, no signal
                self.movingaveragesignl[self.timer]=0
        else:
            if   self.movingaverage_long[self.timer] >= self.movingaverageshort[self.timer]:
                # short was above long, cross over, SELL signal
                self.movingaveragesignl[self.timer]=-1
            else:
                # no crossing, no signal
                self.movingaveragesignl[self.timer]=0

        

        if self.movingaveragesignl[self.timer]==1:
            self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1, ordertype=ORDER_TYPE_MARKET))
        elif self.movingaveragesignl[self.timer]==-1:
            # we do not want to go short first, so we check if we have the stock before we sell
            wehavethestock = self.account.positions.getpositionsofticker(ticker=self.marketdata.tickernames[0])
            if wehavethestock:
                self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=SELL_TO_CLOSE, quantity=1, ordertype=ORDER_TYPE_MARKET))
        else:
            pass

        self.timer+=1
        return self.outgoingorders
        
        

def main():
    myaccounts = [None]*3
    myaccounts[0] = obt.Account(deposit=1000)
    myaccounts[1] = obt.Account(deposit=1000)
    myaccounts[2] = obt.Account(deposit=1000)
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata.rename(columns={'date_eod':'datetime'}, inplace=True)
    stockdata['datetime'] = pd.to_datetime(stockdata['datetime'])

    uniquedaydates = pd.DataFrame(stockdata['datetime'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    ticker = obt.OneTicker(tickername='random', tickertimeseries=stockdata, optionchaintimeseries=pd.DataFrame())
    
    mymarket = obt.Market([ticker],['tic99'])
    mydealer = obt.Dealer(marketdata=mymarket)
    longma = 126
    shrtma = 21
    mystrategies = [None]*3
    mystrategies[0] = MyStrategy(ma_size=len(stockdata), short=7, long=126)
    mystrategies[1] = MyStrategy(ma_size=len(stockdata), short=15, long=30)
    mystrategies[2] = MyStrategy(ma_size=len(stockdata), short=21, long=52)
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccounts, clientstrategies=mystrategies, chronology=uniquedaydates)

    mychronos.primingthestrategyat(longma+1)

    mychronos.execute()

    # print(myaccount.positions.mypositions)
    fig, (ax1,ax2,ax3) = plt.subplots(3,1, sharex=True, sharey=False)
    ax1.plot(uniquedaydates[-len(myaccounts[0].totalvaluests):], myaccounts[0].totalvaluests)
    ax1.plot(uniquedaydates[-len(myaccounts[1].totalvaluests):], myaccounts[1].totalvaluests)
    ax1.plot(uniquedaydates[-len(myaccounts[0].totalvaluests):], myaccounts[2].totalvaluests)
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates, mystrategies[0].movingaverage_long)
    ax2.plot(uniquedaydates, mystrategies[1].movingaverage_long)
    ax2.plot(uniquedaydates, mystrategies[2].movingaverage_long)
    ax2.plot(uniquedaydates, mystrategies[0].movingaverageshort)
    ax2.plot(uniquedaydates, mystrategies[1].movingaverageshort)
    ax2.plot(uniquedaydates, mystrategies[2].movingaverageshort)
    ax2.set_title('Moving Averages')
    ax3.plot(uniquedaydates, mystrategies[0].movingaveragesignl)
    ax3.plot(uniquedaydates, mystrategies[1].movingaveragesignl)
    ax3.plot(uniquedaydates, mystrategies[2].movingaveragesignl)
    ax3.set_title('Buy{1}/Sell{0} signal')
    fig.tight_layout()
    plt.show()
    # plt.plot(uniquedaydates, myaccount.positionvaluests)
    # plt.plot(uniquedaydates, stockdata['close'])
    # plt.show()

    
    print('all orders submitted')
    print(pd.DataFrame(mydealer.orderlistall))
    # [TODO] have the action print as BUY or SELL instead of 1 or -1

    print('\nall orders executed')
    print(pd.DataFrame(mydealer.orderlistexecuted))


    pausehere=1




if __name__ == '__main__':
    main()
