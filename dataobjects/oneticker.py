import numpy as np
import pandas as pd
import datetime

class oneticker():
    """
        oneticker will contain the time series data of a ticker and it's option chain over a specific frequency (daily or intraday)
    """
    def __init__(self, tickername:str, tickertimeseries:pd.DataFrame, optionchaintimeseries:pd.DataFrame) -> None:
        """
            We load the entire data sample at once.
            tickertimeseries would be a pandas.Dataframe timestamp, OHLC with a integer as the index.
        """
        self.ticker = tickername
        self.tickerts = tickertimeseries
        self.optionts = optionchaintimeseries
        self.currenttime = 0

    
    def getnewbar(self) -> dict:
        """
            returns the next candle bar
        """
        self.currenttime+=1


    def resettimer(self) -> None:
        self.currenttime=0
