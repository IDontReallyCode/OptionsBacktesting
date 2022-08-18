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
            self.outgoingorders.append(obt.Order(tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1, ordertype=ORDER_TYPE_MARKET))
        elif self.movingaveragesignl[self.timer]==-1:
            self.outgoingorders.append(obt.Order(tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=SELL_TO_CLOSE, quantity=1, ordertype=ORDER_TYPE_MARKET))
        else:
            pass

        self.timer+=1
        return self.outgoingorders
        
        

def main():
    myaccount = obt.Account(deposit=1000)
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
    mystrategy = MyStrategy(ma_size=len(stockdata), short=shrtma, long=longma)
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(longma+1)

    mychronos.execute()

    print(myaccount.positions.mypositions)
    fig, (ax1,ax2,ax3) = plt.subplots(3,1, sharex=True, sharey=False)
    ax1.plot(uniquedaydates[longma+1:], myaccount.totalvaluests)
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates, mystrategy.movingaverage_long)
    ax2.plot(uniquedaydates, mystrategy.movingaverageshort)
    ax2.set_title('Moving Averages')
    ax3.plot(uniquedaydates, mystrategy.movingaveragesignl)
    ax3.set_title('Buy{1}/Sell{0} signal')
    fig.tight_layout()
    plt.show()
    # plt.plot(uniquedaydates, myaccount.positionvaluests)
    # plt.plot(uniquedaydates, stockdata['close'])
    # plt.show()
    pausehere=1




if __name__ == '__main__':
    main()
