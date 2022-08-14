"""
    This is a basic example:

    Strategy:
        We buy a straddle with the following conditions:
            - we buy on Monday
            - next dte >13
            - we buy the straddle with the maximum Vega
        We sell the straddle:
            - if we managed to buy the straddle
            - we sell on friday
"""

from calendar import weekday
# import numpy as np
import pandas as pd
# from pyparsing import col
import optionbacktesting as obt
# import datetime
import matplotlib.pyplot as plt

class MyStrategy(obt.abstractstrategy.Strategy):


    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)


        optionsnapshot = self.marketdata.SAMPLE.getoptionsnapshot()
        # we want to trade 21+ dte option
        # we filter only those with 21+, then pick the first date because it is sorted by dte
        targetexpdate = optionsnapshot[(optionsnapshot['dte']>=21)].iloc[0]['expirationdate']
        # we want to find the put with delta as close to 20% as possible
        optionsnapshot = optionsnapshot[(optionsnapshot['expirationdate']==targetexpdate) & (optionsnapshot['pcflag']==0)]
        optionsnapshot['deltatrigger'] = (optionsnapshot['delta']+0.20)**2
        trick = optionsnapshot.groupby('k').sum()
        targetstrike = trick['deltatrigger'].idxmin()

        targetput = optionsnapshot[(optionsnapshot['k']==targetstrike) & (optionsnapshot['pcflag']==0) & (optionsnapshot['expirationdate']==targetexpdate)]

        if self.marketdata.currentdatetime.weekday()>=4: #Friday after close => we submit order to open the position
            # Friday has passed, we put an order in for next Monday, buy a put of 14+ dte
            self.theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetput.iloc[0]['symbol'], 
                                    action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetput.iloc[0]['pcflag'], 
                                    k=targetput.iloc[0]['k'], expirationdate=targetput.iloc[0]['expirationdate']))
            self.theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                                    action=obt.BUY_TO_OPEN, quantity=20))

        elif self.marketdata.currentdatetime.weekday() in [0,1,2]: #Monday, Tuesday, Wednesday after close => we adjust hedge
            # we need the option symbol to get the new delta and adjust
            optionpositions = self.account.positions.getoptionpositions(targetput.iloc[0]['ticker'])
            if optionpositions:
                optionsymbol = list(optionpositions.keys())[0]
                optionsnapshot = self.marketdata.SAMPLE.getoptionsnapshot()
                newdelta = optionsnapshot[optionsnapshot['symbol']==optionsymbol].iloc[0]['delta']
                if newdelta<-1:
                    pass
                else:
                    stockposition = self.account.positions.getstockquantityforticker(targetput.iloc[0]['ticker'])
                    quantityadjustementtodeltahedge = -1*(stockposition+(newdelta*100).astype(int))
                    if not quantityadjustementtodeltahedge==0:
                        self.theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                                action=obt.BUY_TO_OPEN, quantity=quantityadjustementtodeltahedge))

        elif self.marketdata.currentdatetime.weekday()==3: #Thursday after close we submit orders to close position
            # Today is Thursday, we put an order to sell Friday (or next opened day)
            sharestosell = self.account.positions.getstockquantityforticker(targetput.iloc[0]['ticker'])
            optionpositions = self.account.positions.getoptionpositions(targetput.iloc[0]['ticker'])
            if optionpositions:
                optionsymbol = list(optionpositions.keys())[0]
                optionstosell = self.account.positions.getoptionquantity(targetput.iloc[0]['ticker'], optionsymbol)
                self.theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol=optionsymbol, 
                                        action=obt.SELL_TO_CLOSE, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetput.iloc[0]['pcflag'], 
                                        k=optionpositions[optionsymbol]['k'], expirationdate=optionpositions[optionsymbol]['expirationdate']))
                self.theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                                        action=obt.SELL_TO_CLOSE, quantity=sharestosell))

        return self.theseorders


def main():
    myaccount = obt.Account(deposit=10000)
    optiondta = pd.read_csv("./SAMPLEdailyoption.csv", index_col=0)
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata['datetime'] = pd.to_datetime(stockdata['date_eod'])
    # TODO  when creating the datetime column, it needs to be a datetime format.
    optiondta['datetime'] = pd.to_datetime(optiondta['date_eod']) # required column
    optiondta.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    optiondta['symbol'] = optiondta['ticker'] + optiondta['pcflag'].astype(str) + optiondta['k'].astype(str) + optiondta['expirationdate']
    uniquedaydates = pd.DataFrame(optiondta['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    tickerSAMPLE = obt.OneTicker(tickername='SAMPLE', tickertimeseries=stockdata, optionchaintimeseries=optiondta)
    
    mymarket = obt.Market([tickerSAMPLE],['SAMPLE']) # <== When dealing with options, we need to have this match the ticker in the option data file
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(1)

    mychronos.execute()


    fig, (ax1,ax2) = plt.subplots(2,1, sharex=True, sharey=False)
    ax1.plot(uniquedaydates[-len(myaccount.totalvaluests):], myaccount.totalvaluests)
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates[-len(myaccount.totalvaluests):],stockdata.iloc[-len(myaccount.totalvaluests):]['close'],label='close')
    ax2.legend()
    ax2.set_title('Stock Price')
    fig.tight_layout()
    plt.show()

    pausehere=1




if __name__ == '__main__':
    main()
