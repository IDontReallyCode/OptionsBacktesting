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
import numpy as np
import pandas as pd
# from pyparsing import col
import optionbacktesting as obt
import datetime


class MyStrategy(obt.abstractstrategy.Strategy):
    def __init__(self) -> None:
        super().__init__()


    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)


        optionsnapshot = self.marketdata.TIC0.getoptionsnapshot()
        # we want to trade 21+ dte option
        # we filter only those with 21+, then pick the first date because it is sorted by dte
        targetexpdate = optionsnapshot[(optionsnapshot['dte']>=21)].iloc[0]['expirationdate']
        # we want to find the straddle with the highest Vega
        optionsnapshot = optionsnapshot[(optionsnapshot['expirationdate']==targetexpdate) & (optionsnapshot['pcflag']==0)]
        optionsnapshot['deltatrigger'] = (optionsnapshot['delta']+0.20)**2
        trick = optionsnapshot.groupby('k').sum()
        targetstrike = trick['deltatrigger'].idxmin()

        targetput = optionsnapshot[(optionsnapshot['k']==targetstrike) & (optionsnapshot['pcflag']==0) & (optionsnapshot['expirationdate']==targetexpdate)]

        doatrade=False
        theseorders = []
        if self.marketdata.currentdatetime.weekday()>=4: #Friday after close => we submit order to open the position
            # Friday has passed, we put an order in for next Monday, buy a put of 14+ dte
            theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetput.iloc[0]['symbol'], 
                                    action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetput.iloc[0]['pcflag'], 
                                    k=targetput.iloc[0]['k'], expirationdate=targetput.iloc[0]['expirationdate']))
            theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                                    action=obt.BUY_TO_OPEN, quantity=20))
            doatrade=True
        elif self.marketdata.currentdatetime.weekday()==0: #Monday after close => we adjust hedge
            # we need the option symbol to get the new delta and adjust
            optionpositions = self.account.positions.getoptionpositions(targetput.iloc[0]['ticker'])
            optionsymbol = list(optionpositions.keys())[0]
            optionsnapshot = self.marketdata.TIC0.getoptionsnapshot()
            newdelta = optionsnapshot[optionsnapshot['symbol']==optionsymbol].iloc[0]['delta']
            stockposition = self.account.positions.getstockquantityforticker(targetput.iloc[0]['ticker'])
            quantityadjustementtodeltahedge = -1*(stockposition+(newdelta*100).astype(int))
            if not quantityadjustementtodeltahedge==0:
                theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                        action=obt.BUY_TO_OPEN, quantity=quantityadjustementtodeltahedge))
                doatrade = True

        elif self.marketdata.currentdatetime.weekday()==1: #Tuesday after close => we adjust hedge
            optionpositions = self.account.positions.getoptionpositions(targetput.iloc[0]['ticker'])
            optionsymbol = list(optionpositions.keys())[0]
            optionsnapshot = self.marketdata.TIC0.getoptionsnapshot()
            newdelta = optionsnapshot[optionsnapshot['symbol']==optionsymbol].iloc[0]['delta']
            stockposition = self.account.positions.getstockquantityforticker(targetput.iloc[0]['ticker'])
            quantityadjustementtodeltahedge = -1*(stockposition+(newdelta*100).astype(int))
            if not quantityadjustementtodeltahedge==0:
                theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                        action=obt.BUY_TO_OPEN, quantity=quantityadjustementtodeltahedge))
                doatrade = True

        elif self.marketdata.currentdatetime.weekday()==2: #Wednesday after close => we adjust hedge
            optionpositions = self.account.positions.getoptionpositions(targetput.iloc[0]['ticker'])
            optionsymbol = list(optionpositions.keys())[0]
            optionsnapshot = self.marketdata.TIC0.getoptionsnapshot()
            newdelta = optionsnapshot[optionsnapshot['symbol']==optionsymbol].iloc[0]['delta']
            stockposition = self.account.positions.getstockquantityforticker(targetput.iloc[0]['ticker'])
            quantityadjustementtodeltahedge = -1*(stockposition+(newdelta*100).astype(int))
            if not quantityadjustementtodeltahedge==0:
                theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                        action=obt.BUY_TO_OPEN, quantity=quantityadjustementtodeltahedge))
                doatrade = True

        elif self.marketdata.currentdatetime.weekday()==3: #Thursday after close we submit orders to close position
            # Today is Thursday, we put an order to sell Friday (or next opened day)
            sharestosell = self.account.positions.getstockquantityforticker(targetput.iloc[0]['ticker'])
            optionpositions = self.account.positions.getoptionpositions(targetput.iloc[0]['ticker'])
            if optionpositions:
                optionsymbol = list(optionpositions.keys())[0]
                optionstosell = self.account.positions.getoptionquantity(targetput.iloc[0]['ticker'], optionsymbol)
                theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetput.iloc[0]['symbol'], 
                                        action=obt.SELL_TO_CLOSE, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetput.iloc[0]['pcflag'], 
                                        k=targetput.iloc[0]['k'], expirationdate=targetput.iloc[0]['expirationdate']))
                theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_STOCK, symbol=targetput.iloc[0]['ticker'], 
                                        action=obt.SELL_TO_CLOSE, quantity=sharestosell))
                doatrade=True
            done=1
            # if self.account.positions.getoptionquantity(targetput.iloc[0]['ticker'], targetcall.iloc[0]['symbol'])>0:
            #     theseorders.append(obt.Order(tickerindex = 0, ticker=targetcall.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetcall.iloc[0]['symbol'], 
            #                             action=obt.SELL_TO_CLOSE, quantity=1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetcall.iloc[0]['pcflag'], 
            #                             k=targetcall.iloc[0]['k'], expirationdate=targetcall.iloc[0]['expirationdate']))
            #     theseorders.append(obt.Order(tickerindex = 0, ticker=targetput.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetput.iloc[0]['symbol'], 
            #                             action=obt.SELL_TO_CLOSE, quantity=1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetput.iloc[0]['pcflag'], 
            #                             k=targetput.iloc[0]['k'], expirationdate=targetput.iloc[0]['expirationdate']))
            #     doatrade=True

        if doatrade:
            return theseorders
        else:
            return []


def main():
    myaccount = obt.Account(deposit=1000)
    optiondtaCLF = pd.read_csv("./privatedata/CLFoc.csv", index_col=0)
    stockdataCLF = pd.read_csv("./privatedata/CLFstock.csv", index_col=0)
    # TODO  when creating the datetime column, it needs to be a datetime format.
    optiondtaCLF['datetime'] = pd.to_datetime(optiondtaCLF['date_eod']) # required column
    optiondtaCLF.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    optiondtaCLF['symbol'] = optiondtaCLF['ticker'] + optiondtaCLF['pcflag'].astype(str) + optiondtaCLF['k'].astype(str) + optiondtaCLF['expirationdate']
    uniquedaydates = pd.DataFrame(optiondtaCLF['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    optiondtaTSLA = pd.read_csv("./privatedata/CLFoc.csv", index_col=0)
    stockdataTSLA = pd.read_csv("./privatedata/CLFstock.csv", index_col=0)
    # TODO  when creating the datetime column, it needs to be a datetime format.
    optiondtaTSLA['datetime'] = pd.to_datetime(optiondtaTSLA['date_eod']) # required column
    optiondtaTSLA.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    optiondtaTSLA['symbol'] = optiondtaTSLA['ticker'] + optiondtaTSLA['pcflag'].astype(str) + optiondtaTSLA['k'].astype(str) + optiondtaTSLA['expirationdate']


    tickerCLF = obt.OneTicker(tickername='CLF', tickertimeseries=stockdataCLF, optionchaintimeseries=optiondtaCLF)
    tickerTSLA = obt.OneTicker(tickername='TSLA', tickertimeseries=stockdataTSLA, optionchaintimeseries=optiondtaTSLA)
    
    mymarket = obt.Market((tickerCLF, tickerTSLA),('TIC0', 'TIC1'), (tickerCLF, tickerCLF, tickerCLF), ("extra1", "extra2", "extra3"))
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(10)

    mychronos.execute()

    pausehere=1




if __name__ == '__main__':
    main()
