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

class strategy(obt.abstractstrategy.strategy):
    def __init__(self) -> None:
        super().__init__()

    def priming(self, index, data):
        pass

    def update(self, data):
        pass


def main():
    myaccount = obt.account(deposit=1000)
    sampledata = pd.read_csv("./privatedata/aaploc.csv", index_col=0)
    tickeraapl = obt.oneticker(tickername='AAPL', tickertimeseries=pd.DataFrame([None]), optionchaintimeseries=sampledata)
    mymarket = obt.market([tickeraapl])
    mydealer = obt.dealer(marketdata=mymarket)
    mystrategy = strategy()
    mychronos = obt.chronos(marketdata=mymarket, marketbroker=mydealer, clientaccount=myaccount, clientstrategy=mystrategy)

    mychronos.primingthestrategyat(10)

    mychronos.execute()

    pausehere=1




if __name__ == '__main__':
    main()
