import numpy as np
import pandas as pd
from .dealer import dealer
from .account import account
from .market import market
from .abstractstrategy import strategy

class chronos():
    """
        chronos will take care of the chronological order and make everything run
        once initialized, you can simply "execute()" and it will run through time and back test the strategy.
        the user can then recuperate:
            - The strategy data will contain the signals that were detected and the orders that were sent to market
            - The dealer data will contain the orders that were sent, and executed
            - the account data will containt the time series evolution of the capital, the margin, (and other metrics as we evolve)
        
        self.chronology is the reference time schedule through which Chronos will go through and make time go by.
    """
    def __init__(self, marketdata:market, marketbroker:dealer, clientaccount:account, clientstrategy:strategy, chronology:pd.DataFrame) -> None:
        self.market = marketdata
        self.broker = marketbroker
        self.account = clientaccount
        self.strategy = clientstrategy
        self.chronology = chronology
        self.currenttime = chronology['datetime'].iloc[0]


    def primingthestrategyat(self, timeindex:int):
        datasofar = self.market.priming(timeindex)
        self.broker.priming(timeindex)
        self.account.priming(timeindex)
        self.strategy.priming(timeindex, self.market.getdatasofar())

        
    def execute(self):

        pass