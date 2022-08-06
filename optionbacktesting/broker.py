from datetime import datetime
import numpy as np
import pandas as pd
from .market import Market
# from .accounts import Position

ASSET_TYPE_STOCK = 0
ASSET_TYPE_OPTION = 1

ORDER_TYPE_MARKET = 0
ORDER_TYPE_LIMIT = 1
ORDER_TYPE_STOP = 2

BUY_TO_OPEN = 1
BUY_TO_CLOSE = 2
BUY_TO_CLOSE_ALL = 3
SELL_TO_OPEN = -1
SELL_TO_CLOSE = -2
SELL_TO_CLOSE_ALL = -3

MARGINTYPE_NONE = 0         # No margin calculated  (In this basic mode, even when shorting a naked call, no margin is calculated)
# TODO MARGINTYPE_TDA = 1          # Follow the guide here : https://www.tdameritrade.com/retail-en_us/resources/pdf/AMTD086.pdf
# TODO MARGINTYPE_PORTFOLIO = 2    # Use a portfolio margin approach based on risk




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
    def __init__(self, void: bool=True, tickerindex:int = 0, assettype:int = ASSET_TYPE_STOCK, action:int = BUY_TO_OPEN, quantity:int = 1, 
                 ordertype:int = ORDER_TYPE_MARKET, triggerprice:int = 0, pcflag:int = 1, k:float = 0, expirationdate:int = 0
                 ) -> None:
        self.void = void
        self.tickerindex = tickerindex
        self.assettype = assettype
        self.action = action
        self.quantity = quantity
        self.ordertype = ordertype
        self.triggerprice = triggerprice
        self.pcflag = pcflag
        self.k = k
        self.expirationdate = expirationdate


class Position():
    def __init__(self, tickerindex: int, assettype: int, quantity: int, pcflag:int = 1, k:float = 0, expirationdate='') -> None:
        self.tickerindex = tickerindex
        self.assettype = assettype
        self.quantity = quantity
        self.pcflag = pcflag
        self.k = k
        self.expirationdate = expirationdate
        pass


class Trade():
    """
        This is just a glorified "change" in position
    """
    def __init__(self, datetime:pd.Timestamp, positionchange:Position, cost:float) -> None:
        self.positionchange = positionchange
        self.cost = cost




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
        self.orderlistwaiting = [None]
        self.orderlistexecuted = [None]


    # def priming(self, currenttime:pd.Timestamp)->int:
    #     self.currentdatetime = currenttime
    #     return self.currentdatetime
        

    def sendorder(self, orderlist:list):
        """
            This is the method through which a strategy sends an order to the dealer to execute
        """
        for eachorder in orderlist:
            if not eachorder.void:
                if self.orderlistwaiting[0] is None:
                    self.orderlistwaiting[0] = eachorder
                else:
                    self.orderlistwaiting.append(eachorder)


            # pass


    # def stepforwardintime(self):
    #     """
    #         Step forward in time will get the lastest candle-bar, then go through the list of order_waiting and see whether any can be executed.
    #     """

    #     alltrades = []

    #     for thisorder in self.orderlistwaiting:
            

    #     return alltrades        
    #     # pass


    def gothroughorders(self):
        """
            Takes the list of 
        """
        alltrades = []
        if self.orderlistwaiting[0] is not None:
            for order in self.orderlistwaiting:
                trade = self.checkorder(order)
                if trade is not None:
                    alltrades.append(trade)
            
            return alltrades
        else:
            return None


    def checkorder(self, thisorder):
        """
            Tries to execute the order within the current candle data
        """
        trade = None
        if thisorder.action==BUY_TO_OPEN:
            if thisorder.assettype==ASSET_TYPE_OPTION:
                if thisorder.ordertype==ORDER_TYPE_MARKET:
                    optionchain = self.market.tickerlist[thisorder.tickerindex].getoptionsnapshot()
                    thisoption = optionchain[(optionchain['pcflag']==thisorder.pcflag) 
                                            & (optionchain['k']==thisorder.k) 
                                            & (optionchain['expirationdate']==thisorder.expirationdate)]
                    tradeprice = thisoption['ask'].iloc[0]
                    totalcost = tradeprice*thisorder.quantity
                    positionchange = Position(tickerindex=thisorder.tickerindex, assettype=thisorder.assettype, quantity=thisorder.quantity,
                                                pcflag = thisorder.pcflag, k=thisorder.k, expirationdate=thisorder.expirationdate)
                    trade = Trade(self.market.currentdatetime, positionchange, totalcost)
                    
            elif thisorder.assettype==ASSET_TYPE_STOCK:
                pass
            else:
                print("What in the actual ?")
                pass
            
        elif thisorder.action==BUY_TO_CLOSE:
            pass

        elif thisorder.action==BUY_TO_CLOSE_ALL:
            pass

        elif thisorder.action==SELL_TO_OPEN:
            pass

        elif thisorder.action==SELL_TO_CLOSE:
            pass

        elif thisorder.action==SELL_TO_CLOSE_ALL:
            pass

        return trade
    




class Account():
    """
        An Account will manage the wealth and the margins
        It will also contain a list of positions
            One position is a dict = {'ticker':ticker,  'quantity':qte}
            ticker is the ticker of the stock, or the composite ticker of the option
            quantity can be positive of negative for long and short positions
    """

    def __init__(self, deposit:float, margintype:int = MARGINTYPE_NONE) -> None:
        self._wealth = deposit
        self.margintype = margintype
        self.margin = 0
        self.positions = [None]
        self.startingtime = 0
        pass


    @property
    def wealth(self):
        return self._wealth

    
    @wealth.setter
    def wealth(self, value):
        self._wealth = value


    def capitalavailable(self) -> float:
        """
            Simply return how much money is available for a trade
        """
        return self.wealth - self.margin


    def margincostoftrade(self, tradedetails:dict)-> float:
        """
            Since this class will have what it takes to deal with margins, the methods to know the margin of a trade will be right in here.
        """
        if self.margintype==0:
            return 0.0
        pass


    def priming(self, currentdatetime:pd.Timestamp):
        self.startingtime = currentdatetime
        return self.startingtime
        
    
    def trade(self, thistrade:list):
        TODO account for the trade
        pass


