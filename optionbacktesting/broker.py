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
    def __init__(self, tickerindex:int, ticker:str, assettype:int, symbol: str, action:int, quantity:int, 
                 ordertype:int = ORDER_TYPE_MARKET, triggerprice:int = 0, pcflag:int = 1, k:float = 0, expirationdate:int = 0
                 ) -> None:
        self.tickerindex = tickerindex
        self.ticker = ticker
        self.assettype = assettype
        self.symbol = symbol
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
    def __init__(self, datetime:pd.Timestamp, positionchange:dict, cashflow:float) -> None:
        self.datetime = datetime
        self.positionchange = positionchange
        self.cashflow = cashflow



class Positions():
    """
    mypositions = {'tic1': {'equity': {'symbol': 'AMD', 'quantity': 5}, 
                            'options': {'optionsymbol1': {'quantity': 5, 'pcflag': 0, 'k':10.0, 'expirationdate':'2000-01-01'}, 
                                    'optionsymbol2': {'quantity': 5, 'pcflag': 0, 'k':20.0, 'expirationdate':'2000-01-01'} }},
                    'tic2': {'equity':{'symbol': 'AAPL', 'quantity': 5}},
                    'tic2': {'options':{'optionsymbol1': {'quantity': 5, 'pcflag': 0, 'k':10.0, 'expirationdate':'2000-01-01'}, 
                                    'optionsymbol2': {'quantity': 5, 'pcflag': 0, 'k':20.0, 'expirationdate':'2000-01-01'} }}
                    }
    """
    def __init__(self) -> None:
        self.mypositions = {}
        pass


    def changestockposition(self, ticker:str, quantity:int):
        # for stocks
        if ticker not in self.mypositions:
            self.mypositions[ticker] = {'equity': {'symbol':ticker, 'quantity':quantity}}
        else:
            if 'equity' in self.mypositions[ticker]:
                self.mypositions[ticker]['equity']['quantity']+=quantity
                if self.mypositions[ticker]['equity']['quantity']==0:
                    self.myposition[ticker].pop('equity')
            else:
                self.mypositions[ticker] = {'equity': {'symbol':ticker, 'quantity':quantity}}

        return self.mypositions


    def changeoptionposition(self, ticker:str, quantity:int, symbol:str, pcflag:int, k:float, expirationdate:pd.Timestamp):
        # for options
        if ticker not in self.mypositions:
            self.mypositions[ticker] = {'options': {symbol: {'quantity': quantity, 'pcflag':pcflag, 'k':k, 'expirationdate':expirationdate}}}
        else:
            if 'options' in self.mypositions[ticker]:
                if symbol in self.mypositions[ticker]['options']:
                    self.mypositions[ticker]['options'][symbol]['quantity']+=quantity
                    if self.mypositions[ticker]['options'][symbol]['quantity']==0:
                        self.mypositions[ticker]['options'].pop(symbol)
                else:
                    self.mypositions[ticker]['options'][symbol] = {'quantity': quantity, 'pcflag':pcflag, 'k':k, 'expirationdate':expirationdate}
            else:
                self.mypositions[ticker]['options'] = {symbol: {'quantity': quantity, 'pcflag':pcflag, 'k':k, 'expirationdate':expirationdate}}
        return self.mypositions


    def getoptionpositions(self, ticker:str, symbol:str=None):
        if ticker in self.mypositions:
            if symbol is None:
                if 'options' in self.mypositions[ticker]:
                    return self.mypositions[ticker]['options']
                else:
                    return {}
            else:
                if 'options' in self.mypositions[ticker]:
                    if symbol in self.mypositions[ticker]['options']:
                        return self.mypositions[ticker]['options'][symbol]
                    else:
                        return {}
                else:
                    return {}
        else:
            return {}


    def getoptionquantity(self, ticker:str, symbol:str):
        if ticker in self.mypositions:
            if 'options' in self.mypositions[ticker]:
                if symbol in self.mypositions[ticker]['options']:
                    return self.mypositions[ticker]['options'][symbol]['quantity']
                else:
                    return 0
            else:
                return 0
        else:
            return 0


    def getpositionsofticker(self, ticker):
        return self.mypositions[ticker]     

    
    def getpositions(self):
        return self.mypositions


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
        self.orderlistwaiting = []
        self.orderlistexecuted = []
        self.optiontradingcost = optiontradingcost


    # def priming(self, currenttime:pd.Timestamp)->int:
    #     self.currentdatetime = currenttime
    #     return self.currentdatetime
        

    def sendorder(self, orderlist:list):
        """
            This is the method through which a strategy sends an order to the dealer to execute
        """
        for eachorder in orderlist:
            # if self.orderlistwaiting[0] is None:
            #     self.orderlistwaiting[0] = eachorder
            # else:
            self.orderlistwaiting.append(eachorder)

        # done=1
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
        stillwaiting = []
        if len(self.orderlistwaiting)>0:
            for index, order in enumerate(self.orderlistwaiting):
                trade = self.checkorder(order)
                if trade is not None:
                    alltrades.append(trade)
                    self.orderlistwaiting[index] = None
                    # del self.orderlistwaiting[index]
                else:
                    stillwaiting.append(order)

            self.orderlistwaiting = stillwaiting
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
                    cashflow = -tradeprice*thisorder.quantity*100
                    positionchange = {'ticker':thisorder.ticker, 'quantity':np.abs(thisorder.quantity), 'assettype':ASSET_TYPE_OPTION,
                                        'pcflag':thisorder.pcflag, 'k':thisorder.k, 'expirationdate':thisorder.expirationdate, 
                                        'symbol':thisorder.symbol}
                                     
                    trade = Trade(self.market.currentdatetime, positionchange, cashflow)
                    
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
                    tradeprice = thisoption['bid'].iloc[0]
                    cashflow = +tradeprice*thisorder.quantity*100
                    positionchange = {'ticker':thisorder.ticker, 'quantity':-np.abs(thisorder.quantity), 'assettype':ASSET_TYPE_OPTION,
                                        'pcflag':thisorder.pcflag, 'k':thisorder.k, 'expirationdate':thisorder.expirationdate, 
                                        'symbol':thisorder.symbol}
                    trade = Trade(self.market.currentdatetime, positionchange, cashflow)


            

        return trade
    




class Account():
    """
        An Account will manage the capital and the margins
        It will also contain a list of positions
            One position is a dict = {'ticker':ticker,  'quantity':qte}
            ticker is the ticker of the stock, or the composite ticker of the option
            quantity can be positive of negative for long and short positions
    """

    def __init__(self, deposit:float, margintype:int = MARGINTYPE_NONE, trackportfoliovalue:bool = False) -> None:
        self._capital = deposit
        self.margintype = margintype
        self.margin = 0
        self.positions = Positions()
        self.startingtime = 0
        self.capitalts = []
        self.trackportfoliovalue = trackportfoliovalue
        # [TODO] add a step tp track the position values at each time step in the chronology
        pass


    @property
    def capital(self):
        return self._capital

    
    @capital.setter
    def capital(self, value):
        self._capital = value


    def capitalavailable(self) -> float:
        """
            Simply return how much money is available for a trade
        """
        return self._capital - self.margin


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
            self.capital += thistrade.cashflow
            self.capitalts.append((thistrade.datetime, self.capital))
            # if we opened a new position, check if we already have a position like that, and add
            # if we closed a position, find the position and remove it
            if thistrade.positionchange['assettype']==ASSET_TYPE_OPTION:
                self.positions.changeoptionposition(thistrade.positionchange['ticker'], thistrade.positionchange['quantity'],
                                            thistrade.positionchange['symbol'], thistrade.positionchange['pcflag'], thistrade.positionchange['k'],
                                            thistrade.positionchange['expirationdate'])
            elif thistrade.positionchange['assettype']==ASSET_TYPE_STOCK:
                self.positions.changestockposition(thistrade.positionchange['ticker'],thistrade.positionchange['quantity'])
        
        return self.capital
        


