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

    def priming(self, index, data):
        super().priming(index, data)
        pass

    def updatedata(self, currentdatetime, dataupdate, marketfeedback, accountfeedback):
        super().updatedata(currentdatetime, dataupdate, marketfeedback, accountfeedback)

        targetexpdate = ""
        if datetime.datetime.strptime(currentdatetime,"%Y-%m-%d").weekday()==0:
            thisorder = obt.Order(void=False, ticker='CLF', assettype=obt.ASSET_TYPE_OPTION, action=obt.BUY_TO_OPEN, 
            quantity=1, ordertype=obt.ORDER_TYPE_MARKET, k=50, expirationdate=targetexpdate)
        elif datetime.datetime.strptime(currentdatetime,"%Y-%m-%d").weekday()==0:
            thisorder = obt.Order(void=False, ticker='CLF', assettype=obt.ASSET_TYPE_OPTION, action=obt.SELL_TO_CLOSE_ALL, 
            quantity=0, ordertype=obt.ORDER_TYPE_MARKET, k=50, expirationdate=targetexpdate)
        else:
            thisorder= obt.Order()
        return thisorder


def main():
    myaccount = obt.Account(deposit=1000)
    sampledata = pd.read_csv("./privatedata/CLFoc.csv", index_col=0)
    # TODO  when creating the datetime column, it needs to be a datetime format.
    sampledata['datetime'] = pd.to_datetime(sampledata['date_eod']) # required column
    sampledata.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    uniquedaydates = pd.DataFrame(sampledata['date_eod'].unique(), columns=['datetime'])

    tickerCLF = obt.OneTicker(tickername='CLF', tickertimeseries=pd.DataFrame(), optionchaintimeseries=sampledata)
    tickerCLF2 = obt.OneTicker(tickername='CLF', tickertimeseries=pd.DataFrame(), optionchaintimeseries=sampledata)
    
    mymarket = obt.Market((tickerCLF, tickerCLF2),('CLF', 'CLF2'))
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketbroker=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(10)

    mychronos.execute()

    pausehere=1




if __name__ == '__main__':
    main()
