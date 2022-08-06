from datetime import datetime
import numpy as np
import pandas as pd
from .market import Market


ASSET_TYPE_STOCK = 0
ASSET_TYPE_OPTION = 1

ORDER_TYPE_MARKET = 0
ORDER_TYPE_LIMIT = 1
ORDER_TYPE_STOP = 2


BUY_TO_OPEN = 1
SELL_TO_CLOSE = 2
SELL_TO_CLOSE_ALL = 3
SELL_TO_OPEN = -1
BUY_TO_CLOSE = -2
BUY_TO_CLOSE_ALL = -3


class Dealer():
    """
        Dealer will deal with receiving orders, holding them in a list, and executing them when possible.
    """
    def __init__(self, marketdata:Market) -> None:
        """
            We initialize the broker/dealer with all the data
        """
        self.market = marketdata
        self.market.resettimer()
        self.currenttime = 0
        self.orderlistwaiting = [None]
        self.orderlistexecuted = [None]


    def priming(self, currenttime:datetime)->int:
        self.currenttime = currenttime
        return self.currenttime
        

    def sendorder(self, order):
        """
            This is the method through which a strategy sends an order to the dealer to execute
        """
        if not order.void:
            self.orderlistwaiting.append(order)
        pass


    def stepforwardintime(self, newtimestep):
        """
            Step forward in time will get the lastest candle-bar, then go through the list of order_waiting and see whether any can be executed.
        """
        # self.currentcandlebar = self.market.getnewbar()
        # self.gothroughorders()
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
    




class Order():
    """
        This is just a glorified Dictionary
        ## Orders
        [FOR NOW AT LEAST]

        An order will be:
            - ticker: str
            - asset type: {stock=0, option=1}
            - position: {long=1, short=-1}
            - quantity: int
            - type: {market=0, limit=1, stop=2}
            - triggerprice: float
    """
    def __init__(self, void: bool=True, ticker:str = "", assettype:int = ASSET_TYPE_STOCK, action:int = BUY_TO_OPEN, quantity:int = 1, 
                 ordertype:int = ORDER_TYPE_MARKET, triggerprice:int = 0, k:float = 0, expirationdate:int = 0
                 ) -> None:
        self.void = void
        self.ticker = ticker
        self.assettype = assettype
        self.action = action
        self.quantity = quantity
        self.ordertype = ordertype
        self.triggerprice = triggerprice
        self.k = k
        self.expirationdate = expirationdate

