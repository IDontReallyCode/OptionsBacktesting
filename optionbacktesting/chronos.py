import numpy as np
import pandas as pd
from .broker import Dealer, Account
# from .accounts import Account
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
    def __init__(self, marketdata:Market, marketdealer:Dealer, clientaccount:Account, clientstrategy:Strategy, chronology:pd.DataFrame) -> None:
        self.market = marketdata
        self.dealer = marketdealer
        self.account = clientaccount
        self.strategy = clientstrategy
        self.chronology = chronology
        self.currenttimestep = 0
        self.currentdatetime = self.chronology['datetime'].iloc[self.currenttimestep]
        self.totaltimesteps = len(chronology)


    def primingthestrategyat(self, timeindex:int):
        """
            Priming the Back Testing Entire System:

            The user needs to know the index winthin the chronology vector, where we start. IT could be at time zero, 
            but it could be later, if we need data to estimate a model prior to start trading.


            Priming the Market:

            Priming the Market simply means setting the "currentdatatime" so the market knows what data is available so far.
        """
        self.currenttimestep = timeindex
        self.currentdatetime = self.chronology['datetime'].iloc[self.currenttimestep]

        self.market.priming(self.currentdatetime)
        # self.dealer.priming(self.currentdatetime)
        self.account.priming(self.currentdatetime)
        self.strategy.priming(self.market)

        
    def execute(self):
        for timeindex in range(self.currenttimestep+1, self.totaltimesteps):
            self.market.timepass(self.chronology['datetime'].iloc[timeindex])
            dealerfeedback = self.dealer.gothroughorders()
            if dealerfeedback is not None:
                accountfeedback = self.account.trade(dealerfeedback)
            else:
                accountfeedback = self.account.wealth
            strategyfeedback = self.strategy.estimatestrategy(dealerfeedback, accountfeedback)
            
            self.dealer.sendorder(strategyfeedback)
        