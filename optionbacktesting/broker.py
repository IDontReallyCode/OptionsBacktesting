# from datetime import datetime
import numpy as np
import pandas as pd

from .market import Market

ASSET_TYPE_STOCK = 0
ASSET_TYPE_OPTION = 1

ORDER_TYPE_MARKET = 0
ORDER_TYPE_LIMIT = 1
ORDER_TYPE_STOP = 2

BUY_TO_OPEN = 1
BUY_TO_CLOSE = 2
SELL_TO_OPEN = -1
SELL_TO_CLOSE = -2
# TODO, for now a BUY is a BUY, to open or close.

MARGINTYPE_NONE = 0         # No margin calculated  (In this basic mode, even when shorting a naked call, no margin is calculated)
MARGINTYPE_TDA = 1          # Follow the guide here : https://www.tdameritrade.com/retail-en_us/resources/pdf/AMTD086.pdf
# TODO MARGINTYPE_PORTFOLIO = 2    # Use a portfolio margin approach based on risk

TRAD_METH_OPTN_WCS = 0      # Buy at ask, sell at bid
TRAD_METH_OPTN_BCS = 1      # Buy at bid, sell at ask
TRAD_METH_OPTN_MID = 2      # Buy and sell and mid price
TRAD_METH_OPTN_25P = 3      # Buy at 25% of bid-ask over bid, sell 25% of bid-ask below ask
TRAD_METH_OPTN_75P = 4      # Buy at 75% of bid-ask over bid, sell 75% of bid-ask below ask
TRAD_METH_OPTN_RND = 5      # Buy and sell at a random price between bid-ask




class Order():
    __orderid = -1
    """
        This is just a glorified Dictionary
        ## Orders
        [FOR NOW AT LEAST]

        An order will be:
            - tickerindex: int      {the index number of the asset, makes things easier for the coding}
            - ticker: str           {Get it from Market.tickernames[tickerindex]}
            - asset type:           {ASSET_TYPE_STOCK = 0, ASSET_TYPE_OPTION = 1}
            - symbol: str           {the ticker for a stock, the unique symbol for an option}
            - action:               {BUY_TO_OPEN = 1, SELL_TO_CLOSE = -1}
            - quantity: int 
            - ordertype:            {ORDER_TYPE_MARKET = 0, ORDER_TYPE_LIMIT = 1, ORDER_TYPE_STOP = 2}
            - tickerprice: float    {Required for margin calculation when shorting options}
            - optionprice: float    {Required for margin calculation when shorting options}
            - triggerprice: float   {for contingent orders}
            - put call flag         {put=0, call=1}
            - strike k
            - expiration date
    """
    def __init__(self, strategyid:int, tickerindex:int, ticker:str, assettype:int, symbol: str, action:int, quantity:int,
                 tickerprice:float = 0.0, optionprice:float = 0.0, ordertype:int = ORDER_TYPE_MARKET, triggerprice:float = 0.0, pcflag:int = 1, k:float = 0, expirationdate:str = ''
                 ) -> None:
        self.strategyid = strategyid                # With multiple strategies at once, we need to identify which strategy submitted which order
        self.tickerindex = tickerindex              # User needs to know the order in which the tickers are loaded
        self.ticker = ticker                        # Ticker string for reference purpose, and dictionary key search
        self.tickerprice = tickerprice              # Required for margin calculation of options
        self.optionprice = optionprice              # Required for margin calculation of options
        self.assettype = assettype                  # ASSET_TYPE_STOCK or ASSET_TYPE_OPTION
        self.symbol = symbol                        # ticker string for stock, the option symbol for options. Required for dictionary key search
        self.action = action                        # BUY or SELL
        self.quantity = quantity                    # no need to explain that one in details.
        self.ordertype = ordertype                  # Market, Limit, Stop
        self.triggerprice = triggerprice            # trigger price for Limit and Stop. Not used for Market orders
        self.pcflag = pcflag                        # Put Call Flag for option
        self.k = k                                  # Strike of option
        self.expirationdate = expirationdate        # expiration date of option
        Order.__orderid +=1
        self.orderid = Order.__orderid

    # to print an order, simply use Order.__dict__
        


class Trade():
    __tradeid = -1
    """
        This is just a glorified dictionary with a positionchange dictionary
    """
    def __init__(self, strategyid:int, datetime:pd.Timestamp, positionchange:dict, cashflow:float) -> None:
        self.strategyid = strategyid
        self.datetime = datetime
        self.positionchange = positionchange
        self.cashflow = cashflow
        Trade.__tradeid +=1
        self.tradeid = Trade.__tradeid



class Positions():
    """
    literally a dictionary...
    mypositions = {'tic1': {'equity': {'symbol': 'AMD', 'quantity': 5, 'tradeprice':18.56}, 
                            'options': {'optionsymbol1': {'quantity': 5, 'pcflag': 0, 'k':10.0, 'expirationdate':'2000-01-01', 'tradeprice':5.56}, 
                                    'optionsymbol2': {'quantity': 5, 'pcflag': 0, 'k':20.0, 'expirationdate':'2000-01-01', 'tradeprice':1.56} }},
                    'tic2': {'equity':{'symbol': 'AAPL', 'quantity': 5, 'tradeprice':154.23}},
                    'tic3': {'options':{'optionsymbol1': {'quantity': 5, 'pcflag': 0, 'k':10.0, 'expirationdate':'2000-01-01', 'tradeprice':0.56}, 
                                    'optionsymbol2': {'quantity': 5, 'pcflag': 0, 'k':20.0, 'expirationdate':'2000-01-01', 'tradeprice':1.56} }}
                    }
    """
    def __init__(self) -> None:
        self.mypositions = {}
        pass


    def _changestockposition(self, tickerid:int, ticker:str, quantity:int, tradeprice:float)->dict:
        # for stocks
        if ticker not in self.mypositions:
            self.mypositions[ticker] = {'equity': {'tickerid':tickerid, 'symbol':ticker, 'quantity':quantity, 'tradeprice':tradeprice}}
        else:
            # We have or had that ticker in our Positions
            if 'equity' in self.mypositions[ticker]:
                # we have that stock in our Positions
                if self.mypositions[ticker]['equity']['quantity']*quantity<0:
                    # We are either selling some of our long shares, or buying back some of our short shares
                    self.mypositions[ticker]['equity']['quantity']+=quantity
                    if self.mypositions[ticker]['equity']['quantity']==0:
                        self.mypositions[ticker].pop('equity')
                else:
                    # We are increasing our position (long or short) and we need to update the average price
                    currentquantity = self.mypositions[ticker]['equity']['quantity']
                    newaveragetradeprice = (currentquantity*self.mypositions[ticker]['equity']['tradeprice'] 
                                            + quantity*tradeprice)/(currentquantity+quantity)
                    self.mypositions[ticker]['equity']['quantity']+=quantity
                    self.mypositions[ticker]['equity']['tradeprice']=newaveragetradeprice
            else:
                # just a new position
                self.mypositions[ticker]['equity'] = {'tickerid':tickerid, 'symbol':ticker, 'quantity':quantity, 'tradeprice':tradeprice}

        return self.mypositions


    def _changeoptionposition(self, tickerid:int, ticker:str, quantity:int, tradeprice:float, symbol:str, pcflag:int, k:float, expirationdate:pd.Timestamp)->dict:
        # for options
        if ticker not in self.mypositions:
            # if ticker is not there at all
            self.mypositions[ticker] = {'options': {symbol: {'tickerid':tickerid, 'quantity': quantity, 'tradeprice':tradeprice, 'pcflag':pcflag, 'k':k, 'expirationdate':expirationdate, 'tradeprice':tradeprice}}}
        else:
            if 'options' in self.mypositions[ticker]:
                if symbol in self.mypositions[ticker]['options']:
                    # That specific option is already in the portfolio, we need to update the quantity and trade price
                    # first we check if we are "adding" to the position, or taking some off.
                    if self.mypositions[ticker]['options'][symbol]['quantity']*quantity<0: # different sign, so we just adjust the quantity
                        self.mypositions[ticker]['options'][symbol]['quantity']+=quantity
                        if self.mypositions[ticker]['options'][symbol]['quantity']==0:
                            self.mypositions[ticker]['options'].pop(symbol)
                    else: # same sign, we are either getting more positive or more negative. either way we need to adjust the average tradeprice.
                        currentquantity = self.mypositions[ticker]['options'][symbol]['quantity']
                        if (currentquantity+quantity)==0:
                            raise Exception("We should not get here. I leave the code, just to check. The if should be removed.")
                        else:
                            newaveragetradeprice = (currentquantity*self.mypositions[ticker]['options'][symbol]['tradeprice'] 
                                                    + quantity*tradeprice)/(currentquantity+quantity)
                            self.mypositions[ticker]['options'][symbol]['quantity']+=quantity
                            self.mypositions[ticker]['options'][symbol]['tradeprice']=newaveragetradeprice
                            if self.mypositions[ticker]['options'][symbol]['quantity']==0:
                                raise Exception("We should not get here. I leave the code, just to check. The if should be removed.")
                                # self.mypositions[ticker]['options'].pop(symbol)
                else:
                    self.mypositions[ticker]['options'][symbol] = {'tickerid':tickerid, 'quantity': quantity, 'tradeprice':tradeprice, 'pcflag':pcflag, 'k':k, 'expirationdate':expirationdate}
            else:
                self.mypositions[ticker]['options'] = {symbol: {'tickerid':tickerid, 'quantity': quantity, 'tradeprice':tradeprice, 'pcflag':pcflag, 'k':k, 'expirationdate':expirationdate}}
        return self.mypositions


    def getoptionpositions(self, ticker:str, symbol:str=None)->dict:
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


    def getoptionsymbols(self, ticker:str)->list[str]:
        if ticker in self.mypositions:
            if 'options' in self.mypositions[ticker]:
                return list[self.mypositions[ticker]['options'].keys()]
            else:
                return []
        else:
            return []


    def getoptionquantity(self, ticker:str, symbol:str)->int:
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


    def getstockposition(self, ticker:str)->dict:
        if ticker in self.mypositions:
            if 'equity' in self.mypositions[ticker]:
                return self.mypositions[ticker]['equity']
        return {}


    def getpositionsofticker(self, ticker:str)->dict:
        if ticker in self.mypositions:
            return self.mypositions[ticker]  
        else:
            return {}   

    
    def getpositions(self)->dict:
        return self.mypositions

    
    def getstockquantityforticker(self, ticker)->int:
        if ticker in self.mypositions:
            if 'equity' in self.mypositions[ticker]:
                return self.mypositions[ticker]['equity']['quantity']
            else:
                return 0
        else:
            return 0



class Dealer():
    """
        Dealer will deal with receiving orders, holding them in a list, and executing them when possible.
    """
    def __init__(self, marketdata:Market, optiontradingcost:float = 0.65, optiontradeprice=TRAD_METH_OPTN_WCS, rngseed=1) -> None:
        """
            We initialize the broker/dealer with all the data
        """
        SEQ = np.random.SeedSequence(rngseed)
        SeedSeq = SEQ.spawn(1)
        self.rngstream = [np.random.default_rng(s) for s in SeedSeq]

        self.market = marketdata
        self.orderlistwaiting = {}
        self.orderlistexecuted = []
        self.orderlistall = []
        self.optiontradingcost = optiontradingcost
        self.tradmethoptn = optiontradeprice


    def sendorder(self, neworderlist:list[Order], orderstoremove:list[Order]=[]):
        """
            This is the method through which a strategy sends an order to the dealer to be executed
        """
        for eachorder in neworderlist:
            # self.orderlistwaiting.append(eachorder)
            # We will check whether the new order should cancel a previous order
            # A buy order on a ticker will cancel both a buy and a sell order on the same ticker
            # A sell order on a ticker will cancel both a buy and a sell order on the same ticker
            thisorderticker = eachorder.ticker
            orderstocancel = []
            for orderid, order in self.orderlistwaiting.items():
                if order.ticker==thisorderticker:
                    orderstocancel.append(self.orderlistwaiting[orderid].orderid)
            for orderid in orderstocancel:
                del self.orderlistwaiting[orderid]
            self.orderlistwaiting[eachorder.orderid] = eachorder
            self.orderlistall.append(eachorder.__dict__)


    def gothroughorders(self)->dict:
        """
            Takes the list of 
        """
        # instead of returning a list of "trades" we can create a dict of trades. with a key for each Strategy
        # we need a dictionary with a key for each strategyid that has trades.
        order: Order

        alltrades = {}
        stillwaiting = {}
        if len(self.orderlistwaiting)>0:
            for index, order in self.orderlistwaiting.items():
                trade = self.checkorder(order)
                if trade is not None:
                    if not order.strategyid in alltrades:
                        alltrades[order.strategyid] = [trade]
                    else:
                        alltrades[order.strategyid].append(trade)
                    self.orderlistexecuted.append(order.__dict__)
                else:
                    stillwaiting[order.orderid] = order

            # overwrite the list of waiting orders by the list of orders still waiting because they were not executed
            self.orderlistwaiting = stillwaiting
            return alltrades
        else:
            return {}


    def checkorder(self, thisorder:Order)->Trade:
        """
            For stocks, at least for now, trade occurs at Open price of the candle
                Remember that the trade occurs in the candle following the timestep when the order was place.
            for options, at least for now, we buy at ask, sell at bid

            [TODO] create a function for getassetprice(), and in that function, allow other methods for trading prices.
        """
        trade = None
        if thisorder.action in [BUY_TO_OPEN, BUY_TO_CLOSE]:
            dobuy=False
            if thisorder.assettype==ASSET_TYPE_OPTION:
                # -------
                #       BUY OPTIONS
                # -------
                if thisorder.ordertype==ORDER_TYPE_MARKET:
                    dobuy=True
                elif thisorder.ordertype==ORDER_TYPE_LIMIT:
                    if tradeprice<=thisorder.triggerprice:
                        dobuy=True
                elif thisorder.ordertype==ORDER_TYPE_STOP:
                    if tradeprice>=thisorder.triggerprice:
                        dobuy=True
                else:
                    raise Exception("What type of order are you trying to do? Use the pre-determined constants")
                
                if dobuy:
                    optionchain = self.market.tickerlist[thisorder.tickerindex].getoptionsnapshot()
                    thisoption = optionchain[(optionchain['pcflag']==thisorder.pcflag) 
                                            & (optionchain['k']==thisorder.k) 
                                            & (optionchain['expirationdate']==thisorder.expirationdate)]
                    # [TODO] This is where we allow for some flexibility in the how trades are executed
                    tradeprice = self.getoptionbuyprice(thisoption.iloc[0])

                    cashflow = -tradeprice*np.abs(thisorder.quantity)*100
                    positionchange = {'tickerid':thisorder.tickerindex, 'ticker':thisorder.ticker, 'quantity':np.abs(thisorder.quantity), 'tradeprice':tradeprice, 'assettype':ASSET_TYPE_OPTION,
                                        'pcflag':thisorder.pcflag, 'k':thisorder.k, 'expirationdate':thisorder.expirationdate, 
                                        'symbol':thisorder.symbol}                                     
                    trade = Trade(thisorder.strategyid, datetime=self.market.currentdatetime, positionchange=positionchange, cashflow=cashflow)

            elif thisorder.assettype==ASSET_TYPE_STOCK:
                # -------
                #       BUY STOCK
                # -------
                candle = self.market.tickerlist[thisorder.tickerindex].getcurrentstockcandle()
                # [TODO] This is where we allow for some flexibility in the how trades are executed
                # [TODO] Adapt the behavior for contingent orders
                tradeprice = candle.iloc[0]['open']

                if thisorder.ordertype==ORDER_TYPE_MARKET:
                    dobuy=True
                elif thisorder.ordertype==ORDER_TYPE_LIMIT:
                    if tradeprice<=thisorder.triggerprice:
                        dobuy=True
                elif thisorder.ordertype==ORDER_TYPE_STOP:
                    if tradeprice>=thisorder.triggerprice:
                        dobuy=True
                else:
                    raise Exception("What type of order are you trying to do? Use the pre-determined constants")

                if dobuy:
                    cashflow = -tradeprice*np.abs(thisorder.quantity)
                    positionchange = {'tickerid':thisorder.tickerindex, 'ticker':thisorder.ticker, 'quantity':np.abs(thisorder.quantity), 'tradeprice':tradeprice, 'assettype':ASSET_TYPE_STOCK,
                                        'symbol':thisorder.ticker}
                    trade = Trade(thisorder.strategyid, self.market.currentdatetime, positionchange, cashflow)
                else:
                    whyamiheredebug=1
            else:
                # Not a stock, not an option
                raise Exception("What in the actual ?")
            
        elif thisorder.action in [SELL_TO_CLOSE, SELL_TO_OPEN]:
            if thisorder.assettype==ASSET_TYPE_OPTION:
                # -------
                #       SELL OPTION
                # -------
                optionchain = self.market.tickerlist[thisorder.tickerindex].getoptionsnapshot()
                thisoption = optionchain[(optionchain['pcflag']==thisorder.pcflag) 
                                        & (optionchain['k']==thisorder.k) 
                                        & (optionchain['expirationdate']==thisorder.expirationdate)]
                tradeprice = self.getoptionsellprice(thisoption.iloc[0])

                dosell = False
                if thisorder.ordertype==ORDER_TYPE_MARKET:
                    dosell=True
                elif thisorder.ordertype==ORDER_TYPE_LIMIT:
                    if tradeprice>=thisorder.triggerprice:
                        dosell=True
                elif thisorder.ordertype==ORDER_TYPE_STOP:
                    if tradeprice<=thisorder.triggerprice:
                        dosell=True
                else:
                    raise Exception("What type of order are you trying to do? Use the pre-determined CONSTANTS ORDER_TYPE_*")
                
                if dosell:
                    cashflow = +tradeprice*np.abs(thisorder.quantity)*100
                    positionchange = {'tickerid':thisorder.tickerindex, 'ticker':thisorder.ticker, 'quantity':-np.abs(thisorder.quantity), 'tradeprice':tradeprice, 'assettype':ASSET_TYPE_OPTION,
                                        'pcflag':thisorder.pcflag, 'k':thisorder.k, 'expirationdate':thisorder.expirationdate, 
                                        'symbol':thisorder.symbol}
                    trade = Trade(thisorder.strategyid, self.market.currentdatetime, positionchange, cashflow)

            elif thisorder.assettype==ASSET_TYPE_STOCK:
                # -------
                #       SELL STOCK
                # -------
                candle = self.market.tickerlist[thisorder.tickerindex].getcurrentstockcandle()
                tradeprice = candle['open'].iloc[0]

                dosell = False
                if thisorder.ordertype==ORDER_TYPE_MARKET:
                    dosell=True
                elif thisorder.ordertype==ORDER_TYPE_LIMIT:
                    if tradeprice>=thisorder.triggerprice:
                        dosell=True
                elif thisorder.ordertype==ORDER_TYPE_STOP:
                    if tradeprice<=thisorder.triggerprice:
                        dosell=True
                else:
                    raise Exception("What type of order are you trying to do? Use the pre-determined constants")

                if dosell:
                    cashflow = +tradeprice*np.abs(thisorder.quantity)
                    positionchange = {'tickerid':thisorder.tickerindex, 'ticker':thisorder.ticker, 'quantity':-np.abs(thisorder.quantity), 'tradeprice':tradeprice, 'assettype':ASSET_TYPE_STOCK,
                                        'symbol':thisorder.ticker}
                    trade = Trade(thisorder.strategyid, self.market.currentdatetime, positionchange, cashflow)
                else:
                    whyamiheredebug=1

            else:
                raise Exception("What in the actual ?")

        return trade
    

    def getoptionbuyprice(self, datarecord:pd.DataFrame)->float:
        if self.tradmethoptn == TRAD_METH_OPTN_WCS:
            tradeprice = datarecord['ask']
        elif self.tradmethoptn == TRAD_METH_OPTN_BCS:
            tradeprice = datarecord['bid']
        elif self.tradmethoptn == TRAD_METH_OPTN_25P:
            tradeprice = datarecord['bid'] + 0.25*(datarecord['ask']-datarecord['bid'])
        elif self.tradmethoptn == TRAD_METH_OPTN_MID:
            tradeprice = datarecord['bid'] + 0.50*(datarecord['ask']-datarecord['bid'])
        elif self.tradmethoptn == TRAD_METH_OPTN_75P:
            tradeprice = datarecord['bid'] + 0.75*(datarecord['ask']-datarecord['bid'])
        elif self.tradmethoptn == TRAD_METH_OPTN_RND:
            tradeprice = datarecord['bid'] + self.rngstream[0].uniform()*(datarecord['ask']-datarecord['bid'])
        else:
            raise Exception("WTF are you trying to do here? This is not even a trade method. Please use the CONSTANTS provided. TRAD_METH_*")
        return tradeprice


    def getoptionsellprice(self, datarecord:pd.DataFrame)->float:
        if self.tradmethoptn == TRAD_METH_OPTN_WCS:
            tradeprice = datarecord['bid']
        elif self.tradmethoptn == TRAD_METH_OPTN_BCS:
            tradeprice = datarecord['ask']
        elif self.tradmethoptn == TRAD_METH_OPTN_25P:
            tradeprice = datarecord['ask'] - 0.25*(datarecord['ask']-datarecord['bid'])
        elif self.tradmethoptn == TRAD_METH_OPTN_MID:
            tradeprice = datarecord['ask'] - 0.50*(datarecord['ask']-datarecord['bid'])
        elif self.tradmethoptn == TRAD_METH_OPTN_75P:
            tradeprice = datarecord['ask'] - 0.75*(datarecord['ask']-datarecord['bid'])
        elif self.tradmethoptn == TRAD_METH_OPTN_RND:
            tradeprice = datarecord['bid'] + self.rngstream[0].uniform()*(datarecord['ask']-datarecord['bid'])
        else:
            raise Exception("WTF are you trying to do here? This is not even a trade method. Please use the CONSTANTS provided. TRAD_METH_*")
        return tradeprice


class Account():
    """
        An Account will manage the capital and the margins
        It will also contain a list of positions
            One position is a dict = {'ticker':ticker,  'quantity':qte}
            ticker is the ticker of the stock, or the composite ticker of the option
            quantity can be positive of negative for long and short positions
    """

    def __init__(self, deposit:float, margintype:int = MARGINTYPE_NONE) -> None:
        self._capital = deposit
        self.margintype = margintype
        self.margin = 0.0
        self.positions = Positions()
        self.positionvalues = 0.0
        self.positionvaluests = []
        self.totalvaluests = []
        self.startingtime = 0
        self.capitalts = []
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


    def priming(self, currentdatetime:pd.Timestamp):
        self.startingtime = currentdatetime
        return self.startingtime
        
    
    def update(self, tradelist:list[Trade])->float:
        """
            Two tasks (for now):
            1- record the trades from the tradelist
        """
        # 1- record the trades from tradelist
        for thistrade in tradelist:
            self.capital += thistrade.cashflow
            self.capitalts.append(self.capital)
            # if we opened a new position, check if we already have a position like that, and add
            # if we closed a position, find the position and remove it
            if thistrade.positionchange['assettype']==ASSET_TYPE_OPTION:
                self.positions._changeoptionposition(thistrade.positionchange['tickerid'], thistrade.positionchange['ticker'], thistrade.positionchange['quantity'], tradeprice=thistrade.positionchange['tradeprice'],
                                            symbol=thistrade.positionchange['symbol'], pcflag=thistrade.positionchange['pcflag'], k=thistrade.positionchange['k'],
                                            expirationdate=thistrade.positionchange['expirationdate'])
            elif thistrade.positionchange['assettype']==ASSET_TYPE_STOCK:
                self.positions._changestockposition(tickerid=thistrade.positionchange['tickerid'] , ticker=thistrade.positionchange['ticker'], 
                                                    quantity=thistrade.positionchange['quantity'], tradeprice=thistrade.positionchange['tradeprice'])
            else:
                raise Exception('It makes no sense to end up here!')

        return self.capital
        

    def estimatemargin(self, order:Order)->float:
        """
            Since this class will have what it takes to deal with margins, the methods to know the margin of a trade will be right in here.
            
            From: https://www.tdameritrade.com/retail-en_us/resources/pdf/AMTD086.pdf
            Uncovered equity options
                Because writing uncovered—or naked—options represents greater risk of loss, the margin account requirements are higher. The writing
                of uncovered puts and calls requires an initial deposit and maintenance of the greatest of the following three formulas:
                a) 20% of the underlying stock²⁷ less the out-of-the-money amount, if any, plus 100% of the current market value of the option(s).
                b) For calls, 10% of the market value of the underlying stock PLUS the premium value. For puts, 10% of the exercise value of the
                underlying stock PLUS the premium value.
                or
                c) $50 per contract plus 100% of the premium.
        """
        # [TODO] Check for all possible combinations of situations
        if self.margintype==MARGINTYPE_NONE:
            return 0.0
        elif self.margintype==MARGINTYPE_TDA:
            if order.assettype == ASSET_TYPE_OPTION:
                if order.pcflag == 1:
                    OTM = np.max(order.tickerprice - order.k, 0)
                    Margin = np.zeros((1,3))
                    Margin[:,0] = 100 * 0.20 * (order.tickerprice - OTM) + order.optionprice
                    Margin[:,1] = (100 * 0.10 * order.k + order.optionprice)
                    Margin[:,2] = (50 + 100*order.optionprice)
                    return np.max(Margin)
                elif order.pcflag == 0:
                    OTM = np.max(order.k - order.tickerprice, 0)
                    Margin = np.zeros((1,3))
                    Margin[:,0] = 100 * 0.20 * (order.tickerprice - OTM) + order.optionprice
                    Margin[:,1] = (100 * 0.10 * order.tickerprice + order.optionprice)
                    Margin[:,2] = (50 + 100*order.optionprice)
                    return np.max(Margin)
                else:
                    raise Exception('This is not an option type')
            elif order.assettype == ASSET_TYPE_STOCK:
                return order.tickerprice*order.quantity*0.5
            else:
                raise Exception('This is not a supported asset type. Use the constants ASSET_TYPE_*')
        else:
            raise Exception('We are not ready to calculate short stock margins')


    def deposit(self, amount:float):
        self._capital += amount

        