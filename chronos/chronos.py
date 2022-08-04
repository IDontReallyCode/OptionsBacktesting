import numpy as np
import pandas as pd
from broker import dealer
from account import account
from dataobjects import market
from strategy import abstractstrategy

class chronos():
    """
        chronos will take care of the chronological order and make everything run
        once initialized, you can simply "execute()" and it will run through time and back test the strategy.
        the user can then recuperate:
            - The strategy data will contain the signals that were detected and the orders that were sent to market
            - The dealer data will contain the orders that were sent, and executed
            - the account data will containt the time series evolution of the capital, the margin, (and other metrics as we evolve)
    """
    def __init__(self, marketdata:market, marketbroker:dealer, clientaccount:account, clientstrategy:abstractstrategy) -> None:
        self.market = marketdata
        self.broker = marketbroker
        self.account = clientaccount
        self.strategy = clientstrategy

        
    def execute(self):
        pass