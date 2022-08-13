"""
    This is a basic example:

    Strategy:
        Buy the stock day 1. hold.
"""

import numpy as np
import pandas as pd
import optionbacktesting as obt
import datetime
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

        historicaldata = self.marketdata.CLF.gettickerdata()
        self.movingaverage_long[0] = np.average(historicaldata.iloc[-self.ma_long__length:]['close'])
        self.movingaverageshort[0] = np.average(historicaldata.iloc[-self.ma_short_length:]['close'])
        self.timer = 1

        

    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)

        lastcandle = self.marketdata.CLF.getcurrentstockcandle()
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
            self.theseorders.append(obt.Order(tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1, ordertype=ORDER_TYPE_MARKET))
        elif self.movingaveragesignl[self.timer]==-1:
            self.theseorders.append(obt.Order(tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                    symbol=self.marketdata.tickernames[0], action=SELL_TO_CLOSE, quantity=1, ordertype=ORDER_TYPE_MARKET))
        else:
            pass

        self.timer+=1
        return self.theseorders
        
        

def main():
    myaccount = obt.Account(deposit=1000)
    stockdataCLF = pd.read_csv("./privatedata/CLFintraday.csv", index_col=0)
    stockdataCLF['datetime'] = pd.to_datetime(stockdataCLF['tdate'])
    stockdataCLF['datetime'] = stockdataCLF['datetime'].dt.tz_localize('UTC').dt.tz_convert("US/Eastern")
    stockdataCLF['date_eod'] = stockdataCLF['datetime'].dt.date
    stockdataCLF['justtimetofilter'] = stockdataCLF['datetime'].dt.time
    stockdataCLF.drop(['total_volume', 'avg_trade_size', 'time_beg', 'vwap', 'opening_price', 'tick_vwap', 'time_end', 'save_date'], axis=1, inplace=True)
    # resample to 5min candles AAAANNNNNDDDDDD make the datetime column the index.
    stockdataCLF = stockdataCLF.resample('1H', on='datetime').last().dropna()
    stockdataCLF.rename(columns={'tick_volume':'volume', 'tick_open':'open', 'tick_close':'close', 'tick_high':'high', 'tick_low':'low'}, inplace=True)
    # filterout pre and post market data
    stockdataCLF = stockdataCLF.between_time(datetime.time(9), datetime.time(15), include_start=True, include_end=True) 

    uniquetimesteps = pd.DataFrame(stockdataCLF['datetime'].unique(), columns=['datetime'])
    uniquetimesteps['datetime'] = pd.to_datetime(uniquetimesteps['datetime'])

    tickerCLF = obt.OneTicker(tickername='CLF', tickertimeseries=stockdataCLF, optionchaintimeseries=pd.DataFrame())
    
    mymarket = obt.Market([tickerCLF],['CLF'])
    mydealer = obt.Dealer(marketdata=mymarket)
    longma = 126
    shrtma = 21
    mystrategy = MyStrategy(ma_size=len(stockdataCLF), short=shrtma, long=longma)
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquetimesteps)

    mychronos.primingthestrategyat(longma+1)

    mychronos.execute()

    print(myaccount.positions.mypositions)
    fig, (ax1,ax2,ax3) = plt.subplots(3,1, sharex=True, sharey=False)
    ax1.plot(uniquetimesteps[longma+1:], myaccount.totalvaluests)
    ax1.set_title('Account value')
    ax2.plot(uniquetimesteps, mystrategy.movingaverage_long)
    ax2.plot(uniquetimesteps, mystrategy.movingaverageshort)
    ax2.set_title('Moving Averages')
    ax3.plot(uniquetimesteps, mystrategy.movingaveragesignl)
    ax3.set_title('Buy{1}/Sell{0} signal')
    fig.tight_layout()
    plt.show()
    # plt.plot(uniquetimesteps, myaccount.positionvaluests)
    # plt.plot(uniquetimesteps, stockdataCLF['close'])
    # plt.show()
    pausehere=1




if __name__ == '__main__':
    main()
