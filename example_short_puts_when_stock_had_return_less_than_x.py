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

import numpy as np
import pandas as pd
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
    # load raw data in some format
    optiondtaCLF = pd.read_csv("./privatedata/CLFoc.csv", index_col=0)
    stockdataCLF = pd.read_csv("./privatedata/CLFintraday.csv", index_col=0)
    # make sure we have the right columns needed for the stock data: ["date_eod", "datetime", "open", "high", "low", "close", "volume"]
    stockdataCLF['datetime'] = pd.to_datetime(stockdataCLF['tdate'])
    stockdataCLF['datetime'] = stockdataCLF['datetime'].dt.tz_localize('UTC').dt.tz_convert("US/Eastern")
    stockdataCLF['date_eod'] = stockdataCLF['datetime'].dt.date
    stockdataCLF['justtimetofilter'] = stockdataCLF['datetime'].dt.time
    stockdataCLF.drop(['total_volume', 'avg_trade_size', 'time_beg', 'vwap', 'opening_price', 'tick_vwap', 'time_end', 'save_date'], axis=1, inplace=True)
    stockdataCLF = stockdataCLF.resample('1H', on='datetime').last().dropna()
    stockdataCLF.rename(columns={'tick_volume':'volume', 'tick_open':'open', 'tick_close':'close', 'tick_high':'high', 'tick_low':'low'}, inplace=True)
    stockdataCLF = stockdataCLF.between_time(datetime.time(6), datetime.time(15), include_start=True, include_end=True)
    # make sure we have the right format for option data: ["date_eod", "datetime", "optionsymbol", "ticker", "pcflag", "k", "dte", "expirationdate", "bid", "ask", "bid_size", "ask_size", "openinterest", "volume"]
    optiondtaCLF['datetime'] = pd.to_datetime(optiondtaCLF['date_eod']) # required column
    optiondtaCLF.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    optiondtaCLF['symbol'] = optiondtaCLF['ticker'] + optiondtaCLF['pcflag'].astype(str) + optiondtaCLF['k'].astype(str) + optiondtaCLF['expirationdate']

    # here we get the time step time series from hourly data.
    uniquetimesteps = pd.DataFrame(stockdataCLF['datetime'].unique(), columns=['datetime'])
    uniquetimesteps['datetime'] = pd.to_datetime(uniquetimesteps['datetime'])
    # find the time step where the option data starts.
    firstoptiondate = optiondtaCLF.iloc[0]['date_eod']


    tickerCLF = obt.OneTicker(tickername='CLF', tickertimeseries=stockdataCLF, optionchaintimeseries=optiondtaCLF)
    
    mymarket = obt.Market((tickerCLF),('CLF'))
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquetimesteps)

    # mychronos.primingthestrategyat(10)

    # mychronos.execute()

    pausehere=1




if __name__ == '__main__':
    main()
