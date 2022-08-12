import numpy as np
import pandas as pd
from .broker import BUY_TO_CLOSE, ORDER_TYPE_MARKET, SELL_TO_CLOSE, Dealer, Account, Order, ASSET_TYPE_OPTION, ASSET_TYPE_STOCK
# from .accounts import Account
from .market import Market
from .abstractstrategy import Strategy

class Chronos():
    """
        chronos will take care of the chronological order and make everything run
        once initialized, you can simply "execute()" and it will run through time and back test the strategy.
        the user can then recuperate:
            - The strategy data will contain the signals that were detected and the orders that were sent to market
            - The dealer data will contain the orders that were sent, and executed
            - the account data will containt the time series evolution of the capital, the margin, (and other metrics as we evolve)
        
        self.chronology is the reference time schedule through which Chronos will go through and make time go by.
    """
    def __init__(self, marketdata:Market, marketdealer:Dealer, clientaccount:Account, clientstrategy:Strategy, chronology:pd.DataFrame) -> None:
        self.market = marketdata
        self.dealer = marketdealer
        self.account = clientaccount
        self.strategy = clientstrategy
        self.chronology = chronology
        self.currenttimestep = 0
        self.currentdatetime = self.chronology['datetime'].iloc[self.currenttimestep]
        self.totaltimesteps = len(chronology)


    def primingthestrategyat(self, timeindex:int):
        """
            Priming the Back Testing Entire System:

            The user needs to know the index winthin the chronology vector, where we start. IT could be at time zero, 
            but it could be later, if we need data to estimate a model prior to start trading.


            Priming the Market:

            Priming the Market simply means setting the "currentdatatime" so the market knows what data is available so far.
        """
        self.currenttimestep = timeindex
        self.currentdatetime = self.chronology['datetime'].iloc[self.currenttimestep]

        self.market.priming(self.currentdatetime)
        # self.dealer.priming(self.currentdatetime)
        self.account.priming(self.currentdatetime)
        self.strategy.priming(self.market, self.account)


    def _updatepositionvalues(self):
        # loop through all positions and fetch the lastest market value
        # [TODO] verify how the value of short positions affect the total value
        totalpositionvalues = 0.0
        for tickers in self.account.positions.mypositions:
            for assettypes in self.account.positions.mypositions[tickers]:
                if assettypes=='equity':
                    lateststockcandle = self.market.__dict__[tickers].getcurrentstockcandle()
                    totalpositionvalues += self.account.positions.mypositions[tickers]['equity']['quantity']*lateststockcandle.iloc[0]['close']
                elif assettypes=='option':
                    for symbols in self.account.positions.mypositions[tickers]['options']:
                        latestoptionsymbolrecord = self.market.__dict__[tickers].getoptionsymbolsnapshot(symbols)
                        done=1
        self.account.positionvalues = totalpositionvalues
        self.account.positionvaluests.append((self.market.currentdatetime, totalpositionvalues))

        
    def execute(self):
        """
            Loops over all time steps in self.chronology
                deals with everything in chronological orders
            
            Then closes all positions
        """
        for timeindex in range(self.currenttimestep+1, self.totaltimesteps):
            self.market.timepass(self.chronology['datetime'].iloc[timeindex])
            dealerfeedback = self.dealer.gothroughorders()
            if dealerfeedback is not None:
                accountfeedback = self.account.update(dealerfeedback)
            else:
                # TODO Check what else we could need here
                accountfeedback = self.account.capital
            strategyfeedback = self.strategy.estimatestrategy(dealerfeedback, accountfeedback)
            
            self._updatepositionvalues()
            self.dealer.sendorder(strategyfeedback)
        
        # closing all positions
        allclosingorders = []
        for tickers in self.account.positions.mypositions:
            for assettypes in self.account.positions.mypositions[tickers]:
                if assettypes=='equity':
                    if self.account.positions.mypositions[tickers][assettypes]['quantity']>0:
                        allclosingorders.append(Order(tickerindex=0, ticker=self.market.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                                        symbol=self.market.tickernames[0], action=SELL_TO_CLOSE, 
                                                        quantity=-self.account.positions.mypositions[tickers][assettypes]['quantity'], 
                                                        ordertype=ORDER_TYPE_MARKET))
                    else:
                        allclosingorders.append(Order(tickerindex=0, ticker=self.market.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                                        symbol=self.market.tickernames[0], action=BUY_TO_CLOSE, 
                                                        quantity=-self.account.positions.mypositions[tickers][assettypes]['quantity'], 
                                                        ordertype=ORDER_TYPE_MARKET))
                elif assettypes=='option':
                    for symbols in self.account.positions.mypositions[tickers]['options']:
                        latestoptionsymbolrecord = self.market.__dict__[tickers].getoptionsymbolsnapshot(symbols)
        
        if len(allclosingorders)>0:
            self.dealer.sendorder(allclosingorders)
            dealerfeedback = self.dealer.gothroughorders()
            if dealerfeedback is not None:
                accountfeedback = self.account.update(dealerfeedback)
            self._updatepositionvalues()
        