# import numpy as np
# import pandas as pd
from abc import ABC
from .market import Market
from .broker import Order, Account

"""
    Can we define here what a strategy should look like, then ask the user to define and code up their own strategy, yet use this in hte chronos class ???
"""

class Strategy(ABC):
    __strategyid = -1
    def __init__(self, outgoingorders:list[Order]=[], waitingorders:list[Order]=[]) -> None:
        """
            A strategy will receive new data through a CALL from chronos.
        """
        self.outgoingorders = outgoingorders
        self.waitingorders = waitingorders
        Strategy.__strategyid += 1
        self.myid = Strategy.__strategyid
        super().__init__()


    def priming(self, marketdata:Market, account:Account):
        """
            Here, the strategy receives the initial set of data which the strategy can use to estimate a model, 
            or whatever it need to start spitting out trading signals
        """
        self.marketdata = marketdata
        self.account = account
        # self.estimatestrategy(None,None)


    def estimatestrategy(self, marketfeedback=None, accountfeedback=None):
        """
            This is where the magic happens

            You access the currently available data from the market by asking self.marketdata
        """
        # optiondata = self.marketdata.tickerlist[0].getoptiondata()
        # Supposed you added data for ticker AAPL, you can also
        #   optiondata = self.marketdata.AAPL.getoptiondata()
        # 
        # You can also provide data for multiple tickers, and name them TIC1, TIC2, TIC3 
        #   optiondata1 = self.marketdata.TIC1.getoptiondata()
        #   optiondata2 = self.marketdata.TIC2.getoptiondata()
        # This way, you can backtest using different tickers, and not have to update your code.
        """
            This method will:
            1- update the data available
            2- receive the feedback from the market, e.g., were the orders sent executed? what are the positions now? etc.
            2- update a model/forecast/whatever
            3- return new instructions/orders for the market if necessary
        """
        # [TODO] Check what we actually need here and not
        self.waitingorders = marketfeedback
        self.accountfeedback = accountfeedback
        self.outgoingorders = []
        return self.outgoingorders
        # pass
