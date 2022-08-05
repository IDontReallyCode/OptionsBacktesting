import numpy as np
import pandas as pd
import datetime

DATA_TYPE_BA = 0
DATA_TYPE_OHLC = 1

class OneTicker():
    """
        oneticker will contain the time series data of a ticker and it's option chain over a specific frequency (daily or intraday)
        
        pd.ticker columns ["date_eod", "timestamp", "open", "high", "low", "close", "volume"]

        pd.opions columns ["date_eod", "timestamp", "]
    """
    def __init__(self, tickername:str, tickertimeseries:pd.DataFrame, optionchaintimeseries:pd.DataFrame, tickerdatatype:int = DATA_TYPE_OHLC, optiondatatype:int = DATA_TYPE_BA) -> None:
        """
            We load the entire data sample at once.
            tickertimeseries HAS TO be a pandas.DataFrame OHLC
            optionchaintimeseries HAS TI be a pandas.DataFrame bid/ask
            See Readme.md for details on the data format
        """
        self.ticker = tickername
        self.tickerts = tickertimeseries
        self.tickertype = tickerdatatype
        self.optionts = optionchaintimeseries
        self.optiontype = optiondatatype
        self.currenttime = 0

    
    # def getnewbar(self) -> dict:
    #     """
    #         returns the next candle bar
    #     """
    #     self.currenttime+=1


    def resettimer(self) -> None:
        """
            [TODO] Figure out the best way to initialize this
        """
        self.currenttime=0


    def getdatapriorto(self, uptotimestamp:datetime):
        stockdata = self.tickerts[self.tickerts["datetime"]<uptotimestamp]
        optiondata = self.optionts[self.optionts["datetime"]<uptotimestamp]
