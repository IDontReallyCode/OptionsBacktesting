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

    def priming(self, market:obt.Market, account:obt.Account):
        super().priming(market, account)
        pass

    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)


        optionsnapshot = self.marketdata.TIC0.getoptionsnapshot()
        # we want to trade 14+ dte option
        # we filter only those with 14+, then pick the first date because it is sorted by dte
        targetexpdate = optionsnapshot[(optionsnapshot['dte']>=14) & (optionsnapshot['pcflag']==1)].iloc[0]['expirationdate']
        targetstrike = 20
        targetoption = optionsnapshot[(optionsnapshot['k']==targetstrike) & (optionsnapshot['pcflag']==1) & (optionsnapshot['expirationdate']==targetexpdate)]

        doatrade=False
        if self.marketdata.currentdatetime.weekday()>=4:
            # Friday has passed, we put an order in for next Monday, buy a put of 14+ dte
            thisorder = obt.Order(tickerindex = 0, ticker=targetoption.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetoption.iloc[0]['symbol'], 
                                    action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetoption.iloc[0]['pcflag'], 
                                    k=targetoption.iloc[0]['k'], expirationdate=targetoption.iloc[0]['expirationdate'])
            doatrade=True
        elif self.marketdata.currentdatetime.weekday()==3:
            # Today is Thursday, we put an order to sell Friday (or next opened day)
            if self.account.positions.getoptionquantity(targetoption.iloc[0]['ticker'], targetoption.iloc[0]['symbol'])>0:
                thisorder = obt.Order(tickerindex = 0, ticker=targetoption.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= targetoption.iloc[0]['symbol'], 
                                        action=obt.SELL_TO_CLOSE, quantity=1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=targetoption.iloc[0]['pcflag'], 
                                        k=targetoption.iloc[0]['k'], expirationdate=targetoption.iloc[0]['expirationdate'])
                doatrade=True

        if doatrade:
            return [thisorder]
        else:
            return []


def main():
    myaccount = obt.Account(deposit=1000)
    sampledata = pd.read_csv("./privatedata/CLFoc.csv", index_col=0)
    # TODO  when creating the datetime column, it needs to be a datetime format.
    sampledata['datetime'] = pd.to_datetime(sampledata['date_eod']) # required column
    sampledata.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    sampledata['symbol'] = sampledata['ticker'] + sampledata['pcflag'].astype(str) + sampledata['k'].astype(str) + sampledata['expirationdate']
    uniquedaydates = pd.DataFrame(sampledata['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    tickerCLF = obt.OneTicker(tickername='CLF', tickertimeseries=pd.DataFrame(), optionchaintimeseries=sampledata)
    tickerCLF2 = obt.OneTicker(tickername='CLF2', tickertimeseries=pd.DataFrame(), optionchaintimeseries=sampledata)
    
    mymarket = obt.Market((tickerCLF, tickerCLF2),('TIC0', 'TIC1'), (tickerCLF, tickerCLF, tickerCLF), ("extra1", "extra2", "extra3"))
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(10)

    mychronos.execute()

    pausehere=1




if __name__ == '__main__':
    main()
