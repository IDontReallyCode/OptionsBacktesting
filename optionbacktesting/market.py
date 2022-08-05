import numpy as np
import pandas as pd
import datetime

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