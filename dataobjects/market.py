import numpy as np
import pandas as pd

class market():
    """
        The market class will contain the data for multiple tickers
    """
    def __init__(self, tickerlist:list) -> None:
        """
            After loading the data of one or more tickers (including the option chains), we "package" then toghether into one object that we call "market"
        """
        self.tickerlist = tickerlist
        for eachticker in self.tickerlist:
            eachticker.resettimer()
        self.currenttime = 0


    def priming(self, timeindex:int):
        """
            time step to which we jump because that data was used to initialize the strategy
        """
        self.currenttime = timeindex
        return self.currenttime


    def getdatasofar(self)->pd.DataFrame:
        """
            Returns all the data that is in the past
        """
        pass


    def getnewbar(self) -> list:
        """
            Will get the next timestep data from each ticker and return a list with the data
        """
        pass


    def resettimer(self) -> None:
        self.currenttime = 0
        pass