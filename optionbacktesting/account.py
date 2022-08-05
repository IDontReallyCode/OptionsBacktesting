import numpy as np
import pandas as pd

MARGINTYPE_NONE = 0         # No margin calculated  (In this basic mode, even when shorting a naked call, no margin is calculated)
# TODO MARGINTYPE_TDA = 1          # Follow the guide here : https://www.tdameritrade.com/retail-en_us/resources/pdf/AMTD086.pdf
# TODO MARGINTYPE_PORTFOLIO = 2    # Use a portfolio margin approach based on risk


class account():
    """
        An account will manage the wealth and the margins
        It will also contain a list of positions
            One position is a dict = {'ticker':ticker,  'quantity':qte}
            ticker is the ticker of the stock, or the composite ticker of the option
            quantity can be positive of negative for long and short positions
    """

    def __init__(self, deposit:float, margintype:int = MARGINTYPE_NONE) -> None:
        self._wealth = deposit
        self.margintype = margintype
        self.margin = 0
        self.positions = [None]
        pass


    @property
    def wealth(self):
        return self._wealth

    
    @wealth.setter
    def wealth(self, value):
        self._wealth = value


    def capitalavailable(self) -> float:
        """
            Simply return how much money is available for a trade
        """
        return self.wealth - self.margin


    def margincostoftrade(self, tradedetails:dict)-> float:
        """
            Since this class will have what it takes to deal with margins, the methods to know the margin of a trade will be right in here.
        """
        if self.margintype==0:
            return 0.0
        pass


    def priming(self, timestep:int):
        pass