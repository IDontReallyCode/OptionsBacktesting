import numpy as np
import pandas as pd
import datetime

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
            optionchaintimeseries HAS TI be a pandas.DataFrame bid/ask
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
        self.currentdatetime = currentdatetime


    # def getdatapriorto(self, uptotimestamp:datetime):
    #     stockdata = self.tickerts[self.tickerts["datetime"]<uptotimestamp]
    #     optiondata = self.optionts[self.optionts["datetime"]<uptotimestamp]

    def gettickerdata(self):
        return self._tickerts[self._tickerts["datetime"]<=self.currentdatetime]


    def getoptiondata(self):
        return self._optionts[self._optionts["datetime"]<=self.currentdatetime]


    def getoptionsnapshot(self):
        thisday = str(self.currentdatetime.date())
        return self._optionts[self._optionts["datetime"]==thisday]

    
    def getcurrentstockcandle(self):
        thisday = str(self.currentdatetime.date())
        return self._tickerts[self._tickerts["datetime"]==thisday]

    
    def getoptionsymbolsnapshot(self, symbol):
        thisday = str(self.currentdatetime.date())
        return self._optionts[(self._optionts["datetime"]==thisday) & (self._optionsts['symbol']==symbol)]