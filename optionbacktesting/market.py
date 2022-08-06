import numpy as np
import pandas as pd
import datetime



class Market():
    """
        The market class will contain the data for multiple tickers
    """
    def __init__(self, tickerlist:list, tickernames:list) -> None:
        """
            After loading the data of one or more tickers (including the option chains), we "package" then toghether into one object that we call "market"
        """
        if not len(tickerlist) == len(tickernames):
            print("WTF is wrong with you")
            pass
        for index, eachtick in enumerate(tickernames):
            setattr(self, eachtick, tickerlist[index])

        self.currenttime = 0


    def priming(self, currenttimestamp:datetime):
        """
            time step to which we jump because that data was used to initialize the strategy
            for each ticker in the tickerlist
                get the data up to the timeindex and return that
        """
        self.currenttime = currenttimestamp

        return self.currenttime


    def getdatasofar(self, newtimestamp = None)->pd.DataFrame:
        """
            Returns all the data that is in the past
        """
        # if newtimestamp is not None:
        #     self.currenttime = newtimestamp

        # tickerdatasofar = [None]*self.nbtickers
        # optiondatasofar = [None]*self.nbtickers
        # for index, eachticker in enumerate(self.tickerlist):
        #     if not eachticker.tickerts.empty:
        #         tickerdatasofar[index] = eachticker.tickerts[eachticker.tickerts['datetime']<self.currenttime]
        #     if not eachticker.optionts.empty:    
        #         optiondatasofar[index] = eachticker.optionts.loc[eachticker.optionts['datetime']<self.currenttime]

        # # [TODO] Analyse and decide whether we should return the data this way, or simply provide the currenttimestamp and have the strategy retrieve the data from the market class
        # return tickerdatasofar, optiondatasofar
        pass


    def timepass(self, currentdatetime) -> list:
        """
            Will get the next timestep data from each ticker and return a list with the data
        """
        self.currenttime = currentdatetime

        return self.currenttime



    def resettimer(self) -> None:
        self.currenttime = 0
        pass



