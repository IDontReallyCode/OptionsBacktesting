import numpy as np
import pandas as pd
from dataobjects import market


class dealer():
    """
        Dealer will deal with receiving orders, holding them in a list, and executing them when possible.
    """
    def __init__(self, marketdata:market) -> None:
        """
            We initialize the broker/dealer with all the data
        """
        self.market = marketdata
        self.market.resettimer()
        self.currenttime = 0
        self.orderlistwaiting = [None]
        self.orderlistexecuted = [None]


    def priming(self, timeindex:int)->int:
        self.currenttime = timeindex
        return self.currenttime
        

    def sendorder(self, order):
        """
            This is the method through which a strategy sends an order to the dealer to execute
        """
        self.orderlistwaiting.append(order)
        pass


    def stepforwardintime(self):
        """
            Step forward in time will get the lastest candle-bar, then go through the list of order_waiting and see whether any can be executed.
        """
        self.currentcandlebar = self.market.getnewbar()
        self.gothroughorders()
        pass


    def gothroughorders(self):
        """
            Takes the list of 
        """
        for order in self.orderlistwaiting:
            self.checkorder(order)


    def checkorder(self, order):
        """
            Tries to execute the order within the current candle data
        """
        pass
    
