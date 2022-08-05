import numpy as np
import pandas as pd
import datetime


ASSET_TYPE_STOCK = 0
ASSET_TYPE_OPTION = 1

ORDER_TYPE_MARKET = 0
ORDER_TYPE_LIMIT = 1
ORDER_TYPE_STOP = 2

BUY_LONG = 1
SELL_SHORT = -1

class Market():
    """
        The market class will contain the data for multiple tickers
    """
    def __init__(self, tickerlist:list) -> None:
        """
            After loading the data of one or more tickers (including the option chains), we "package" then toghether into one object that we call "market"
        """
        self.tickerlist = tickerlist
        self.nbtickers = len(tickerlist)
        for eachticker in self.tickerlist:
            eachticker.resettimer()
        self.currenttime = 0


    def priming(self, currenttimestamp:datetime):
        """
            time step to which we jump because that data was used to initialize the strategy
            for each ticker in the tickerlist
                get the data up to the timeindex and return that
        """
        self.currenttime = currenttimestamp

        return self.getdatasofar()


    def getdatasofar(self, newtimestamp = None)->pd.DataFrame:
        """
            Returns all the data that is in the past
        """
        if newtimestamp is not None:
            self.currenttime = newtimestamp

        tickerdatasofar = [None]*self.nbtickers
        optiondatasofar = [None]*self.nbtickers
        for index, eachticker in enumerate(self.tickerlist):
            if not eachticker.tickerts.empty:
                tickerdatasofar[index] = eachticker.tickerts[eachticker.tickerts['datetime']<self.currenttime]
            if not eachticker.optionts.empty:    
                optiondatasofar[index] = eachticker.optionts[eachticker.optionts['datetime']<self.currenttime]

        # [TODO] Analyse and decide whether we should return the data this way, or simply provide the currenttimestamp and have the strategy retrieve the data from the market class
        return tickerdatasofar, optiondatasofar


    def getnewbar(self) -> list:
        """
            Will get the next timestep data from each ticker and return a list with the data
        """
        pass


    def resettimer(self) -> None:
        self.currenttime = 0
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
    def __init__(self, ticker, assettype:int =ASSET_TYPE_STOCK, position:int =BUY_LONG, quantity:int = 1, ordertype:int = ORDER_TYPE_MARKET, triggerprice=0) -> None:
        self.ticker = ticker
        self.assettype = assettype
        self.position = position
        self.quantity = quantity
        self.ordertype = ordertype
        self.triggerprice = triggerprice

