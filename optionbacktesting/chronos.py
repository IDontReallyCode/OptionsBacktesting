import numpy as np
import pandas as pd
from .dealer import Dealer
from .accounts import Account
from .market import Market
from .abstractstrategy import Strategy

class Chronos():
    """
        chronos will take care of the chronological order and make everything run
        once initialized, you can simply "execute()" and it will run through time and back test the strategy.
        the user can then recuperate:
            - The strategy data will contain the signals that were detected and the orders that were sent to market
            - The dealer data will contain the orders that were sent, and executed
            - the account data will containt the time series evolution of the capital, the margin, (and other metrics as we evolve)
        
        self.chronology is the reference time schedule through which Chronos will go through and make time go by.
    """
    def __init__(self, marketdata:Market, marketbroker:Dealer, clientaccount:Account, clientstrategy:Strategy, chronology:pd.DataFrame) -> None:
        self.market = marketdata
        self.broker = marketbroker
        self.account = clientaccount
        self.strategy = clientstrategy
        self.chronology = chronology
        self.currenttime = self.chronology['datetime'].iloc[0]


    def primingthestrategyat(self, timeindex:int):
        self.currenttime = self.chronology['datetime'].iloc[timeindex]

        datasofar = self.market.priming(self.currenttime)
        self.broker.priming(self.currenttime)
        self.account.priming(self.currenttime)
        self.strategy.priming(self.currenttime, datasofar)

        
    def execute(self):

        pass