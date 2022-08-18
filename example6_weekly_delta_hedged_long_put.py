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

# from calendar import weekday
import numpy as np
import pandas as pd
# from pyparsing import col
import optionbacktesting as obt
# import datetime
import matplotlib.pyplot as plt

class MyStrategy(obt.abstractstrategy.Strategy):

    def __init__(self) -> None:
        super().__init__()
        self.buydates = []
        self.selldates = []
        self.stockpositions = []
        self.deltavalues = []

    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)


        self.stockpositions.append(self.account.positions.getstockquantityforticker(self.marketdata.tickernames[0]))


        if self.marketdata.currentdatetime.weekday()>=4: #Friday after close => we submit order to open the position
            # unless the previous position was not closed
            currentoptionpositions = self.account.positions.getoptionpositions(self.marketdata.tickernames[0])
            if not currentoptionpositions:
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
                self.deltavalues.append(targetput.iloc[0]['delta'])
                # Friday has passed, we put an order in for next Monday, buy a put of 14+ dte
                self.outgoingorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetput.iloc[0]['symbol'], 
                                        action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetput.iloc[0]['pcflag'], 
                                        k=targetput.iloc[0]['k'], expirationdate=targetput.iloc[0]['expirationdate']))
                self.outgoingorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                                        action=obt.BUY_TO_OPEN, quantity=20))
                self.buydates.append((self.marketdata.currentdatetime))

        elif self.marketdata.currentdatetime.weekday() in [0,1,2]: #Monday, Tuesday, Wednesday after close => we adjust hedge
            # we need the option symbol to get the new delta and adjust
            optionpositions = self.account.positions.getoptionpositions(self.marketdata.tickernames[0])
            if optionpositions:
                optionsymbol = list(optionpositions.keys())[0]
                optionsnapshot = self.marketdata.SAMPLE.getoptionsnapshot()
                newdelta = optionsnapshot[optionsnapshot['symbol']==optionsymbol].iloc[0]['delta']
                
                if newdelta<-1:
                    pass
                else:
                    self.deltavalues.append(newdelta)
                    stockposition = self.account.positions.getstockquantityforticker(self.marketdata.tickernames[0])
                    quantityadjustementtodeltahedge = -1*(stockposition+(newdelta*100).astype(int))
                    if quantityadjustementtodeltahedge>0:
                        self.outgoingorders.append(obt.Order(tickerindex = 0, ticker=self.marketdata.tickernames[0], assettype=obt.ASSET_TYPE_STOCK, symbol=self.marketdata.tickernames[0], 
                                action=obt.BUY_TO_OPEN, quantity=abs(quantityadjustementtodeltahedge)))
                    else:
                        self.outgoingorders.append(obt.Order(tickerindex = 0, ticker=self.marketdata.tickernames[0], assettype=obt.ASSET_TYPE_STOCK, symbol=self.marketdata.tickernames[0], 
                                action=obt.SELL_TO_CLOSE, quantity=abs(quantityadjustementtodeltahedge)))
                    

        elif self.marketdata.currentdatetime.weekday()==3: #Thursday after close we submit orders to close position
            # Today is Thursday, we put an order to sell Friday (or next opened day)
            sharestosell = self.account.positions.getstockquantityforticker(self.marketdata.tickernames[0])
            optionpositions = self.account.positions.getoptionpositions(self.marketdata.tickernames[0])
            if optionpositions:
                optionsymbol = list(optionpositions.keys())[0]
                optionstosell = self.account.positions.getoptionquantity(self.marketdata.tickernames[0], optionsymbol)
                self.outgoingorders.append(obt.Order(tickerindex = 0, ticker=self.marketdata.tickernames[0], assettype=obt.ASSET_TYPE_OPTION, symbol=optionsymbol, 
                                        action=obt.SELL_TO_CLOSE, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=optionpositions[optionsymbol]['pcflag'], 
                                        k=optionpositions[optionsymbol]['k'], expirationdate=optionpositions[optionsymbol]['expirationdate']))
                self.outgoingorders.append(obt.Order(tickerindex = 0, ticker=self.marketdata.tickernames[0], assettype=obt.ASSET_TYPE_STOCK, symbol=self.marketdata.tickernames[0], 
                                        action=obt.SELL_TO_CLOSE, quantity=sharestosell))
                self.selldates.append((self.marketdata.currentdatetime))
                self.deltavalues.append(0)
        return self.outgoingorders


def main():
    myaccount = obt.Account(deposit=2000)
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


    fig, (ax1,ax2,ax3,ax4,ax5) = plt.subplots(5,1, sharex=False, sharey=False)
    ax1.plot(uniquedaydates[-len(myaccount.totalvaluests):], myaccount.totalvaluests)
    ax1.yaxis.set_major_formatter('${x:1.2f}')
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates[-len(myaccount.totalvaluests):],stockdata.iloc[-len(myaccount.totalvaluests):]['close'],label='close')
    ax2.yaxis.set_major_formatter('${x:1.2f}')
    ax2.legend()
    ax2.set_title('Stock Price')
    ax3.plot(uniquedaydates[-len(mystrategy.stockpositions):], mystrategy.stockpositions)
    ax3.set_title('Stock positions')
    ax4.plot(uniquedaydates[-len(mystrategy.deltavalues):], mystrategy.deltavalues)
    ax4.set_title('Delta values')
    ax5.stem(mystrategy.buydates,1*np.ones(len(mystrategy.buydates),),linefmt='green')
    ax5.stem(mystrategy.selldates,-1*np.ones(len(mystrategy.selldates),),linefmt='red')
    ax4.set_title('Buy and sells of the put')
    fig.tight_layout()
    fig.suptitle('Buy a put on Monday, Delta hedge it all week, close position on Friday')
    plt.show()


    
    print('all orders submitted')
    print(pd.DataFrame(mydealer.orderlistall))
    # [TODO] have the action print as BUY or SELL instead of 1 or -1

    print('\nall orders executed')
    print(pd.DataFrame(mydealer.orderlistexecuted))



    pausehere=1




if __name__ == '__main__':
    main()
