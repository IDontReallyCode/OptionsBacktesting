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
# from pyparsing import col
import optionbacktesting as obt

class MyStrategy(obt.abstractstrategy.Strategy):
    def __init__(self) -> None:
        super().__init__()

    def priming(self, index, data):
        super().priming(index, data)
        pass

    def update(self, data):
        pass


def main():
    myaccount = obt.Account(deposit=1000)
    sampledata = pd.read_csv("./privatedata/CLFoc.csv", index_col=0)
    # TODO  when creating the datetime column, it needs to be a datetime format.
    sampledata['datetime'] = sampledata['date_eod'] # required column
    sampledata.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    uniquedaydates = pd.DataFrame(sampledata['date_eod'].unique(), columns=['datetime'])

    tickeraapl = obt.OneTicker(tickername='AAPL', tickertimeseries=pd.DataFrame(), optionchaintimeseries=sampledata)
    mymarket = obt.Market([tickeraapl])
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = MyStrategy()
    mychronos = obt.Chronos(marketdata=mymarket, marketbroker=mydealer, clientaccount=myaccount, clientstrategy=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(10)

    mychronos.execute()

    pausehere=1




if __name__ == '__main__':
    main()
