# import numpy as np
import pandas as pd
from .market import Market
from .broker import *
from .abstractstrategy import Strategy

class Chronos():
    """
        chronos will take care of the chronological order and make everything run
        once initialized, you can simply "execute()" and it will run through time and back test the strategylist.
        the user can then recuperate:
            - The strategylist data will contain the signals that were detected and the orders that were sent to market
            - The dealer data will contain the orders that were sent, and executed
            - the accountlist data will containt the time series evolution of the capital, the margin, (and other metrics as we evolve)
        
        self.chronology is the reference time schedule through which Chronos will go through and make time go by.
    """
    def __init__(self, marketdata:Market, marketdealer:Dealer, clientaccounts:list[Account], clientstrategies:list[Strategy], chronology:pd.DataFrame) -> None:
        self.market = marketdata
        self.dealer = marketdealer
        if not type(clientstrategies) is list:
            raise Exception('Please submit a list of strategies, as long as a list of accounts of the same lenth, even if you only have one strategy')
        self.nbstrategies = len(clientstrategies)
        if not len(clientaccounts)==self.nbstrategies:
            raise Exception('Please submit as many account copies as strategy copies')
        self.accountlist = clientaccounts
        self.strategylist = clientstrategies
        self.chronology = chronology
        self.startingtimestep = 0
        self.startingdatetime = self.chronology['datetime'].iloc[self.startingtimestep]
        self.totaltimesteps = len(chronology)


    def primingthestrategyat(self, timeindex:int):
        """
            Priming the Back Testing Entire System:

            The user needs to know the index winthin the chronology vector, where we start. IT could be at time zero, 
            but it could be later, if we need data to estimate a model prior to start trading.


            Priming the Market:

            Priming the Market simply means setting the "currentdatatime" so the market knows what data is available so far.
        """
        self.startingtimestep = timeindex
        self.startingdatetime = self.chronology['datetime'].iloc[self.startingtimestep]

        self.market.priming(self.startingdatetime)
        for index in range(self.nbstrategies):
            self.accountlist[index].priming(self.startingdatetime)
            self.strategylist[index].priming(self.market, self.accountlist[index])


    def _updatepositionvalues(self):
        # loop through all positions and fetch the lastest market value
        # [TODO] verify how the value of short positions affect the total value
        for index in range(self.nbstrategies):
            totalpositionvalues = 0.0
            for tickers in self.accountlist[index].positions.mypositions:
                for assettypes in self.accountlist[index].positions.mypositions[tickers]:
                    if assettypes=='equity':
                        lateststockcandle = self.market.__dict__[tickers].getcurrentstockcandle()
                        totalpositionvalues += self.accountlist[index].positions.mypositions[tickers]['equity']['quantity']*lateststockcandle.iloc[0]['close']
                    elif assettypes=='options':
                        for symbols in self.accountlist[index].positions.mypositions[tickers]['options']:
                            latestoptionsymbolrecord = self.market.__dict__[tickers].getoptionsymbolsnapshot(symbols)
                            markprice = (latestoptionsymbolrecord.iloc[0]['bid'] + latestoptionsymbolrecord.iloc[0]['ask'])/2
                            totalpositionvalues += self.accountlist[index].positions.mypositions[tickers]['options'][symbols]['quantity']*markprice*100

            self.accountlist[index].positionvalues = totalpositionvalues
            self.accountlist[index].positionvaluests.append(totalpositionvalues)
            self.accountlist[index].totalvaluests.append(self.accountlist[index].capital+totalpositionvalues)

        
    def execute(self):
        """
            Loops over all time steps in self.chronology
                deals with everything in chronological orders
            
            Then closes all positions
        """
        for timeindex in range(self.startingtimestep+1, self.totaltimesteps):
            # 1. Tell the `Market` to move one step in time by passing the next `['datetime']`
            self.market.timepass(self.chronology['datetime'].iloc[timeindex])

            tradelist = self.dealer.gothroughorders()

            if len(tradelist)>0:
                check=1

            for index in range(self.nbstrategies):
                # 2. Tell the `Dealer` execute orders.
                # if tradelist[] is not None:
                #     # 3. Tell the `Account` to update based on the `Trade`s 
                if index in tradelist:
                    accountfeedback = self.accountlist[index].update(tradelist[index])
                else:
                    accountfeedback = []
                    tradelist[index] = []
                # else:
                #     # TODO Check what else we could need here
                    # accountfeedback = self.accountlist.capital
                # 4. Tell the `Strategy` to update,    
                strategyfeedback = self.strategylist[index].estimatestrategy(tradelist[index], accountfeedback)
                
                self.dealer.sendorder(strategyfeedback)

            self._updatepositionvalues()


        # closing all positions
        for index in range(self.nbstrategies):
            allclosingorders = []
            for tickers in self.accountlist[index].positions.mypositions:
                for assettypes in self.accountlist[index].positions.mypositions[tickers]:
                    if assettypes=='equity':
                        if self.accountlist[index].positions.mypositions[tickers][assettypes]['quantity']>0:
                            allclosingorders.append(Order(index, tickerindex=0, ticker=self.market.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                                            symbol=self.market.tickernames[0], action=SELL_TO_CLOSE, 
                                                            quantity=-self.accountlist[index].positions.mypositions[tickers][assettypes]['quantity'], 
                                                            ordertype=ORDER_TYPE_MARKET))
                        else:
                            allclosingorders.append(Order(index, tickerindex=0, ticker=self.market.tickernames[0], assettype=ASSET_TYPE_STOCK, 
                                                            symbol=self.market.tickernames[0], action=BUY_TO_CLOSE, 
                                                            quantity=-self.accountlist[index].positions.mypositions[tickers][assettypes]['quantity'], 
                                                            ordertype=ORDER_TYPE_MARKET))
                    elif assettypes=='option':
                        for symbols in self.accountlist[index].positions.mypositions[tickers]['options']:
                            latestoptionsymbolrecord = self.market.__dict__[tickers].getoptionsymbolsnapshot(symbols)
        
            if len(allclosingorders)>0:
                self.dealer.sendorder(allclosingorders)
                tradelist = self.dealer.gothroughorders()
                if tradelist is not None:
                    if index in tradelist:
                        accountfeedback = self.accountlist[index].update(tradelist[index])
                    else:
                        accountfeedback = []
                        tradelist[index] = []
                self._updatepositionvalues()
        