import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataobjects import market
from account import account

"""
    ???????????????????????
    Can we define here what a strategy should look like, then ask the user to define and code up their own strategy, yet use this in hte chronos class ???
    ???????????????????????
"""

class strategy(ABC):
    def __init__(self, currentdata:market, clientaccount:account) -> None:
        """
            A strategy will receive new data through a CALL from chronos.
        """
        super().__init__()


    def updatedata(self, dataupdate, marketfeedback):
        """
            This method will:
            1- update the data available
            2- receive the feedback from the market, e.g., were the orders sent executed? what are the positions now? etc.
            2- update a model/forecast/whatever
            3- return new instructions/orders for the market if necessary
        """
        pass