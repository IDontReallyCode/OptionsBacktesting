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
SELL_TO_OPEN = -1
SELL_TO_CLOSE = -2

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



class Trade():
    """
        This is just a glorified "change" in position
    """
    def __init__(self, datetime:pd.Timestamp, positionchange:dict, cost:float) -> None:
        self.datetime = datetime
        self.positionchange = positionchange
        self.cost = cost



class Positions():
    def __init__(self) -> None:
        self.nbpositions    = 0
        self.tickerindex    = []
        self.symbol         = []
        self.pcflag         = []
        self.k              = []
        self.expirationdate = []
        self.quantity       = []
        pass


    def changeposition(self, quantity, tickerindex, symbol, pcflag:int = 1, k:float = 0, expirationdate:pd.Timestamp = pd.to_datetime('2000-01-01')):
        if symbol in self.symbol:
            where = self.symbol.index(symbol)
            self.quantity[where] += quantity
            if self.quantity[where]==0:
                del self.tickerindex[where]
                del self.symbol[where]
                del self.pcflag[where]
                del self.k[where]
                del self.expirationdate[where]
                del self.quantity[where]
                self.nbpositions -= 1
        else:
            self.tickerindex.append(tickerindex)
            self.symbol.append(symbol)
            self.pcflag.append(pcflag)
            self.k.append(k)
            self.expirationdate.append(expirationdate)
            self.quantity.append(quantity)
            self.nbpositions+=1

        return self.nbpositions


    def getpositionofsymbol(self, symbol):
        if symbol in self.symbol:
            return self.quantity[self.symbol.index(symbol)]
        else:
            return 0


    def getpositionsofticker(self, tickerindex):
        outtickerindex    = []
        outsymbol         = []
        outpcflag         = []
        outk              = []
        outexpirationdate = []
        outquantity       = []
        if tickerindex in self.tickerindex:
            # where = self.tickerindex.index(tickerindex)
            indices = [i for i, x in enumerate(self.tickerindex) if x == tickerindex]
            for index in indices:
                outtickerindex.append(self.tickerindex[index])    
                outsymbol.append(self.symbol[index])         
                outpcflag.append(self.pcflag[index])         
                outk.append(self.k[index])              
                outexpirationdate.append(self.expirationdate[index]) 
                outquantity.append(self.quantity[index])       

        return outtickerindex, outsymbol, outpcflag, outk, outexpirationdate, outquantity      


class Dealer():
    """
        Dealer will deal with receiving orders, holding them in a list, and executing them when possible.
    """
    def __init__(self, marketdata:Market, optiontradingcost:float = 0.65) -> None:
        """
            We initialize the broker/dealer with all the data
        """
        self.market = marketdata
        self.market.resettimer()
        self.orderlistwaiting = [None]
        self.orderlistexecuted = [None]
        self.optiontradingcost = optiontradingcost


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
            for index, order in enumerate(self.orderlistwaiting):
                trade = self.checkorder(order)
                if trade is not None:
                    alltrades.append(trade)
                    self.orderlistwaiting[index] = None
            self.orderlistwaiting = filter(None, self.orderlistwaiting)

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
                    totalcost = -tradeprice*thisorder.quantity
                    positionchange = {'tickerindex':thisorder.tickerindex, 'assettype':thisorder.assettype,
                                        'pcflag':thisorder.pcflag, 'k':thisorder.k, 'expirationdate':thisorder.expirationdate, 
                                        'quantity':thisorder.quantity
                                     }
                    trade = Trade(self.market.currentdatetime, positionchange, totalcost)
                    
            elif thisorder.assettype==ASSET_TYPE_STOCK:
                pass
            else:
                print("What in the actual ?")
                pass
            
        elif thisorder.action==BUY_TO_CLOSE:
            pass

        elif thisorder.action==SELL_TO_OPEN:
            pass

        elif thisorder.action==SELL_TO_CLOSE:
            if thisorder.assettype==ASSET_TYPE_OPTION:
                if thisorder.ordertype==ORDER_TYPE_MARKET:
                    optionchain = self.market.tickerlist[thisorder.tickerindex].getoptionsnapshot()
                    thisoption = optionchain[(optionchain['pcflag']==thisorder.pcflag) 
                                            & (optionchain['k']==thisorder.k) 
                                            & (optionchain['expirationdate']==thisorder.expirationdate)]
                    tradeprice = thisoption['ask'].iloc[0]
                    totalcost = +tradeprice*thisorder.quantity
                    positionchange = {'tickerindex':thisorder.tickerindex, 'assettype':thisorder.assettype,
                                        'pcflag':thisorder.pcflag, 'k':thisorder.k, 'expirationdate':thisorder.expirationdate, 
                                        'quantity':thisorder.quantity
                                     }
                    trade = Trade(self.market.currentdatetime, positionchange, totalcost)


            

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
        self.positions = dict.fromkeys(['tickerindex', 'assettype', 'pcflag', 'k', 'expirationdate','quantity'])
        self.startingtime = 0
        self.wealthts = []
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
        
    
    def trade(self, tradelist:list):
        for thistrade in tradelist:
            self.wealth += thistrade.cost
            self.wealthts.append((thistrade.datetime, self.wealth))
            # if we opened a new position, check if we already have a position like that, and add
            # if we closed a position, find the position and remove it
        
        return self.wealth
        


