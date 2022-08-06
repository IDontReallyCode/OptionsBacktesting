import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from .market import Market
# from account import account
from .dealer import Order

"""
    ???????????????????????
    Can we define here what a strategy should look like, then ask the user to define and code up their own strategy, yet use this in hte chronos class ???
    ???????????????????????
"""

class Strategy(ABC):
    def __init__(self) -> None:
        """
            A strategy will receive new data through a CALL from chronos.
        """
        self.data = pd.DataFrame([None])
        self.timeindex = 0
        self.outgoingorders = [None]
        self.waitingorders = [None]

        super().__init__()


    def priming(self, marketdata:Market):
        """
            Here, the strategy receives the initial set of data which the strategy can use to estimate a model, 
            or whatever it need to start spitting out trading signals
        """
        self.marketdata = marketdata
        self.estimatestrategy()


    def estimatestrategy(self):
        """
            This is where the magic happens

            You access the currently available data from the market by asking self.marketdata
        """
        pass


    def updatedata(self, marketfeedback, accountfeedback):
        """
            This method will:
            1- update the data available
            2- receive the feedback from the market, e.g., were the orders sent executed? what are the positions now? etc.
            2- update a model/forecast/whatever
            3- return new instructions/orders for the market if necessary
        """
        self.waitingorders = marketfeedback
        self.accountfeedback = accountfeedback
        theseorders = Order(void=True)
        return theseorders