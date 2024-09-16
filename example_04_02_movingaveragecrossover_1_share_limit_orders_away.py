"""
    This is a basic example:

    Strategy:
        Use moving averages crossover to generate buy/sell signals
        Buy the stock when the short moving average crosses above the long moving average
        Sell the stock when the short moving average crosses below the long moving average
        Hold otherwise
        Use limit orders, limit_buy at 10% below clsoe, limit_sell at 10% above close

        Now, here, we need to manage that if we create a new order, we need to cancel a previous order that was not executed.
"""


import numpy as np
import pandas as pd
import optionbacktesting as obt
# import datetime
import matplotlib.pyplot as plt
import matplotlib.axes as axes

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
        self.tradebuylist = []
        self.tradesellist = []


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
            mylimit = lastcandle.iloc[0]['close']*0.90
            myorder = obt.Order(strategyid=self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                symbol=self.marketdata.tickernames[0], action=BUY_TO_OPEN, quantity=1, ordertype=ORDER_TYPE_LIMIT, triggerprice=mylimit)
            self.tradebuylist.append(myorder.orderid)
            self.outgoingorders.append(myorder)
        elif self.movingaveragesignl[self.timer]==-1:
            # we do not want to go short first, so we check if we have the stock before we sell
            wehavethestock = self.account.positions.getpositionsofticker(ticker=self.marketdata.tickernames[0])
            if wehavethestock:
                mylimit = lastcandle.iloc[0]['close']*1.10
                myorder = obt.Order(strategyid=self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], assettype=ASSET_TYPE_STOCK,
                                    symbol=self.marketdata.tickernames[0], action=SELL_TO_CLOSE, quantity=1, ordertype=ORDER_TYPE_LIMIT, triggerprice=mylimit)
                self.tradesellist.append(myorder.orderid)
                self.outgoingorders.append(myorder)
        else:
            pass

        self.timer+=1
        return self.outgoingorders
        
        

def main():
    myaccount = [obt.Account(deposit=1000)]
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
    mystrategy = [MyStrategy(ma_size=len(stockdata), short=shrtma, long=longma)]
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccount, clientstrategies=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(longma+1)

    mychronos.execute()

    ax1: axes._axes.Axes
    ax2: axes._axes.Axes
    ax3: axes._axes.Axes
    print(myaccount[0].positions.mypositions)
    fig, (ax1,ax2,ax3) = plt.subplots(3,1, sharex=True, sharey=False)
    # ax1.plot(uniquedaydates[-len(myaccount[0].totalvaluests):], myaccount[0].totalvaluests)
    total_value_padded = np.pad(myaccount[0].totalvaluests, (len(uniquedaydates) - len(myaccount[0].totalvaluests), 0), 'constant', constant_values=(0,))
    ax1.plot(uniquedaydates, total_value_padded)
    ax1.set_title('Account value')
    ax1.set_ylim(min(myaccount[0].totalvaluests)-20, max(total_value_padded) + 20)

    # when we prime the strategy, we set the vector as long as the market data, but we set the timer to 1.
    # Thus, everything is shifted, and we need to pad the signal to match the length that we skipped to prime the strategy
    mysignal = mystrategy[0].movingaveragesignl
    mysignal[longma+1:] = mystrategy[0].movingaveragesignl[0:-longma-1]
    mysignal[0:longma] = 0

    buy_signals = np.where(mysignal == 1)[0]
    sell_signals = np.where(mysignal == -1)[0]

    
    ax1.stem(uniquedaydates.loc[buy_signals, 'datetime'], 
             np.full_like(buy_signals, max(total_value_padded) + 20), 
             linefmt='g-', markerfmt='go', basefmt=' ', bottom=min(myaccount[0].totalvaluests)-20)
    ax1.stem(uniquedaydates.loc[sell_signals, 'datetime'], 
             np.full_like(sell_signals, max(total_value_padded) + 20), 
             linefmt='r-', markerfmt='ro', basefmt=' ', bottom=min(myaccount[0].totalvaluests)-20)
    ma_long_padded = mystrategy[0].movingaverage_long
    mashort_padded = mystrategy[0].movingaverageshort
    ma_long_padded[longma+1:] = mystrategy[0].movingaverage_long[0:-longma-1]
    mashort_padded[longma+1:] = mystrategy[0].movingaverageshort[0:-longma-1]
    ma_long_padded[0:longma] = 0
    mashort_padded[0:longma] = 0
    ax2.plot(uniquedaydates, ma_long_padded)
    ax2.plot(uniquedaydates, mashort_padded)
    ax2.set_title('Moving Averages')
    ax3.plot(uniquedaydates, mysignal)
    ax3.set_title('Buy{1}/Sell{0} signal')
    fig.tight_layout()
    plt.show()
    # plt.plot(uniquedaydates[-len(myaccount[0].totalvaluests):], myaccount[0].positionvaluests)
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
