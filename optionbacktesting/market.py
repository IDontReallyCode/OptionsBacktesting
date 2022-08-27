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
        self.currentdatetime = pd.Timestamp


    def settime(self, currentdatetime:pd.Timestamp) -> None:
        """
            currentdatetime must come from the Chronos.chronology, which has the time series of all time steps to run through for the back testing
            Setting the time will ensure you get the right data when you need too.
        """
        self.currentdatetime = currentdatetime


    def getstockdata(self) -> pd.DataFrame:
        """
            returns all the underlying stock data up until the current datetime
        """
        return self._tickerts[self._tickerts["datetime"]<=self.currentdatetime]


    def getoptiondata(self) -> pd.DataFrame:
        """
            returns all the option data up until the current datetime
        """
        return self._optionts[self._optionts["datetime"]<=self.currentdatetime]


    def getoptionsnapshot(self) -> pd.DataFrame:
        """
            returns the currentdatetime snapshot for the option chain
        """
        snapshot = self._optionts[self._optionts["datetime"]==self.currentdatetime]
        if snapshot.empty:
            sofar = self._optionts[self._optionts["datetime"]<=self.currentdatetime]
            lasttimestamp = sofar.iloc[-1]['datetime']
            snapshot = self._optionts[self._optionts['datetime']==lasttimestamp]

        return snapshot

    
    def getcurrentstockcandle(self) -> pd.DataFrame:
        """
            Returns only the last candle
        """
        candle = self._tickerts[self._tickerts["datetime"]==self.currentdatetime]
        if candle.empty:
            sofar = self._tickerts[self._tickerts["datetime"]<=self.currentdatetime]
            candle = sofar.iloc[-1:]
        return candle

    
    def getoptionsymbolsnapshot(self, symbol) -> pd.DataFrame:
        """
            Get the latest optin snapshot, but only for 1 specific option, based on it's unique symbol
        """
        snapshot = self._optionts[(self._optionts["datetime"]==self.currentdatetime) & (self._optionts['symbol']==symbol)]
        if snapshot.empty:
            sofar = self._optionts[(self._optionts["datetime"]<=self.currentdatetime) & (self._optionts['symbol']==symbol)]
            lasttimestamp = sofar.iloc[-1]['datetime']
            snapshot = sofar[self._optionts['datetime']==lasttimestamp]

        return snapshot


    def verifydata(self):
        """
            Verifies the DataFrames for the right columns and data types
        """
        # [TODO]
        pass


    def stocktimeseriestoplot(self) -> np.ndarray:
        x = np.array(self._tickerts['datetime'])
        y = np.array(self._tickerts['close'])
        return x, y


class Market():
    """
        The market class will contain the data for multiple tickers
    """
    def __init__(self, tickerlist:list[OneTicker], tickernames:list[str], ExtraData:list = [], ExtraNames:list = []) -> None:
        """
            After loading the data of one or more tickers (including the option chains), we "package" then toghether into one object that we call "market"

            Suppose you have Data for QQQ and TQQQ (in that order)

            You can access the data using self.QQQ, or self.tickerlist[0]

            Internally, self.tickerlist[0] will be used.
            However, the user, when creating their Strategy class/object, they will be able to access the data using the ticker name directly
        """
        if type(tickerlist) is not list:
            raise Exception("Please submit as a list, even if there is only one ticker. I am too lazy to convert your arguments!")
        if not len(tickerlist) == len(tickernames):
            print("WTF is wrong with you")
            pass
        if not len(ExtraData) == len(ExtraNames):
            print("WTF is wrong with you")
            pass
        self.tickernames = tickernames
        self.tickerlist = tickerlist
        for index, eachtick in enumerate(tickernames):
            setattr(self, eachtick, tickerlist[index])

        for index, eachname in enumerate(ExtraNames):
            setattr(self, eachname, ExtraData[index])

        self.currentdatetime = None


    def priming(self, currenttimestamp:pd.Timestamp):
        """
            time step to which we jump because that data was used to initialize the strategy
            for each ticker in the tickerlist
                get the data up to the timeindex and return that
        """
        self.currentdatetime = currenttimestamp
        # for index, eachtick in enumerate(self.tickernames):
        for index in range(len(self.tickernames)):
            self.tickerlist[index].settime(currenttimestamp)


    def timepass(self, currentdatetime:pd.Timestamp) -> None:
        """
            update the new datetime for the market, but also each ticker
        """
        self.currentdatetime = currentdatetime
        for index, eachtick in enumerate(self.tickernames):
            self.tickerlist[index].settime(currentdatetime)


    # def resettimer(self) -> None:
    #     self.currentdatetime = datetime.datetime.today()
    #     pass



