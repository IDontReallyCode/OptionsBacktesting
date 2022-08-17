# import numpy as np
import pandas as pd
# import datetime

DATA_TYPE_BA = 0
DATA_TYPE_OHLC = 1

class OneTicker():
    """
        oneticker will contain the time series data of a ticker and it's option chain over a specific frequency (daily or intraday)
        
        pd.ticker columns ["date_eod", "datetime", "open", "high", "low", "close", "volume"]

        pd.opions columns ["date_eod", "datetime", "ticker", "pcflag", "k", "dte", "expirationdate", "bid", "ask", "bid_size", "ask_size", "openinterest", "volume"]
    """
    def __init__(self, tickername:str, tickertimeseries:pd.DataFrame, optionchaintimeseries:pd.DataFrame, tickerdatatype:int = DATA_TYPE_OHLC, optiondatatype:int = DATA_TYPE_BA) -> None:
        """
            We load the entire data sample at once.
            tickertimeseries HAS TO be a pandas.DataFrame OHLC
            optionchaintimeseries HAS TO be a pandas.DataFrame bid/ask
            See Readme.md for details on the data format
        """
        self.ticker = tickername
        self._tickerts = tickertimeseries
        self.tickertype = tickerdatatype
        self._optionts = optionchaintimeseries
        self.optiontype = optiondatatype
        self.currentdatetime = pd.Timestamp

    
    def resettimer(self) -> None:
        """
            [TODO] Figure out the best way to initialize this
        """
        self.currentdatetime=0


    def settime(self, currentdatetime):
        """
            currentdatetime must come from the Chronos.chronology, which has the time series of all time steps to run through for the back testing
            Setting the time will ensure you get the right data when you need too.
        """
        self.currentdatetime = currentdatetime


    def getstockdata(self):
        """
            returns all the underlying stock data up until the current datetime
        """
        return self._tickerts[self._tickerts["datetime"]<=self.currentdatetime]


    def getoptiondata(self):
        """
            returns all the option data up until the current datetime
        """
        return self._optionts[self._optionts["datetime"]<=self.currentdatetime]


    def getoptionsnapshot(self):
        """
            returns the currentdatetime snapshot for the option chain
        """
        thisday = str(self.currentdatetime.date())
        return self._optionts[self._optionts["datetime"]==thisday]
        # [TODO] Update this to work for both daily and intrady data

    
    def getcurrentstockcandle(self):
        """
            Returns only the last candle
        """
        candle = self._tickerts[self._tickerts["datetime"]==self.currentdatetime]
        if candle.empty:
            sofar = self._tickerts[self._tickerts["datetime"]<=self.currentdatetime]
            candle = sofar.iloc[-1:]
        return candle

    
    def getoptionsymbolsnapshot(self, symbol):
        """
            Get the latest optin snapshot, but only for 1 specific option, based on it's unique symbol
        """
        thisday = str(self.currentdatetime.date())
        return self._optionts[(self._optionts["datetime"]==thisday) & (self._optionsts['symbol']==symbol)]


    def verifydata(self):
        """
            Verifies the DataFrames for the right columns and data types
        """
        # [TODO]
        pass