"""
    This is a basic example:

    Strategy:
        We buy a straddle with the following conditions:
            - we buy on Monday
            - next dte >13
            - we buy the straddle with the maximum Vega
        We sell the straddle:
            - if we managed to buy the straddle
            - we sell on friday
"""

# from calendar import weekday
import numpy as np
import pandas as pd
# from pyparsing import col
import optionbacktesting as obt
import datetime
import matplotlib.pyplot as plt

class MyStrategy(obt.abstractstrategy.Strategy):

    def __init__(self, ratioRV_tohedge, ratioPNL_takeprofit, ratioPNL_takeloss, ratioRV_takeloss) -> None:
        super().__init__()
        self.buydates = []
        self.selldates = []
        self.stockpositions = []
        self.deltavalues = []
        self.currentRV = 0
        self.ratioRV_tohedge = ratioRV_tohedge
        self.ratioPNL_takeprofit = ratioPNL_takeprofit
        self.ratioPNL_takeloss = ratioPNL_takeloss
        self.ratioRV_takeloss = ratioRV_takeloss

    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)

        """
            Strategy, 
            Estimate RV using realized Volatility from previous day
            Estimate IV using the average IV of ATM options with roughly 30 dte
            Short a straddle with the highest total VEGA, with roughly 45 dte
            We keep until it's about 2 dte,
            OR we realized 50% gain on the premium from the entire position, including stock used to hedge
            OR we lost 100% of premium value and RV/IV < threshold#2

            If RV/IV > threshold#1, we delta hedge the position
            else, we let it be
        """
        if marketfeedback:
            # [TODO] We need a way to track the straddle position and calculate the return
            check=1
        # 1- Calculate the Realized Volatility from intraday data
        #       We need to make sure we have at least one day of data,
        #       This is easy since the option data starts later than the stock data. So after priming the system, we have what we need

        stockdata = self.marketdata.tickerlist[0].getstockdata()
        # check if we are at the first candle of the day to calculate RV from previous day
        if not stockdata.iloc[-2]['date_eod']==stockdata.iloc[-1]['date_eod']:
            # we are at the first candle of the day. filter out the data from yesterday
            previousdaycloses = np.array(stockdata[stockdata['date_eod']==stockdata.iloc[-2]['date_eod']]['close'])
            logreturnsquared = np.log(previousdaycloses[1:]/previousdaycloses[:-1])**2
            realizedannualvolatility = np.sqrt(np.sum(logreturnsquared)*252)*100

            self.currentRV = realizedannualvolatility
        
        if self.currentRV==0:
            return self.outgoingorders

        # Calculate current IV based on current option snapshot
        optionsnapshot = self.marketdata.tickerlist[0].getoptionsnapshot()

        # get the DTE closest to 30
        targetexpdate = optionsnapshot[(optionsnapshot['dte']>=25)].iloc[0]['expirationdate']
        onemonthoptions = optionsnapshot[(optionsnapshot['expirationdate']==targetexpdate)]
        # get moneyness between .95 and 1.05
        onemonthoptions['moneyness'] = onemonthoptions['k']/stockdata.iloc[-1]['close']
        ATMoptions = onemonthoptions[(onemonthoptions['moneyness']>=0.95) & (onemonthoptions['moneyness']<=1.05)]
        IV = np.mean(ATMoptions['volatility'])

        # Check whether we have a straddle position
        currentposition = self.account.positions.getoptionpositions(self.marketdata.tickernames[0])
        if currentposition:
            closethis = False
            # we have a position, check how to deal with it
            # get the remaining dte
            # putsnapshot = self.account.positions.getoptionpositions(ticker=self.marketdata.tickernames[0], symbol=list(currentposition)[0])
            checkdte = self.marketdata.tickerlist[0].getoptionsymbolsnapshot(symbol=list(currentposition)[0])
            stockposition = self.account.positions.getstockposition(self.marketdata.tickernames[0])
            stockcandle = self.marketdata.tickerlist[0].getcurrentstockcandle()
            dte = checkdte.iloc[0]['dte']
            if stockposition:
                stockquantity = stockposition['quantity']
                stocktradeprice = stockposition['tradeprice']
            else:
                stockquantity = 0
                stocktradeprice = 0

            if dte<3:
                # let's close this
                closethis = True

            # calculate profits/loss so far AND calculate total delta
            # if PNL > A, we close all
            # if PNL < B, we close all
            profits = 0
            initial = 0
            totaldelta = 0
            for eachkey in currentposition:
                optionsnapshot = self.marketdata.tickerlist[0].getoptionsymbolsnapshot(symbol=eachkey)
                initial += currentposition[eachkey]['tradeprice']*100
                profits += (currentposition[eachkey]['tradeprice'] - optionsnapshot.iloc[0]['ask'])*100
                totaldelta += optionsnapshot.iloc[0]['delta']*100

            profits += stockquantity*(stockcandle.iloc[0]['close'] - stocktradeprice)
            initial += stockquantity*(stocktradeprice)

            totalreturn = profits/initial
            # if RV/IV > thresholdHEDGE, we hedge
            if totalreturn>self.ratioPNL_takeprofit:
                closethis = True

            if (totalreturn<self.ratioPNL_takeloss) and (self.currentRV/IV<self.ratioRV_takeloss):
                closethis = True

            if closethis:
                for keys in currentposition:
                    self.outgoingorders.append(obt.Order(self.myid, 0, self.marketdata.tickernames[0], obt.ASSET_TYPE_OPTION, keys,
                            obt.BUY_TO_CLOSE, quantity=1, tickerprice=0, optionprice=0, 
                            ordertype=obt.ORDER_TYPE_MARKET, pcflag=currentposition[keys]['pcflag'], k=currentposition[keys]['k'], 
                            expirationdate=currentposition[keys]['expirationdate']))
                if stockquantity>0:
                    self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], symbol=self.marketdata.tickernames[0],
                    assettype = obt.ASSET_TYPE_STOCK, action=obt.SELL_TO_OPEN, quantity = totaldelta, ordertype=obt.ORDER_TYPE_MARKET))
                elif stockquantity<0:
                    self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], symbol=self.marketdata.tickernames[0],
                    assettype = obt.ASSET_TYPE_STOCK, action=obt.BUY_TO_OPEN, quantity = totaldelta, ordertype=obt.ORDER_TYPE_MARKET))

            if (self.currentRV/IV > self.ratioRV_tohedge):
                # we hedge
                totaldelta = int(totaldelta)
                deltadelta = stockquantity + totaldelta

                if deltadelta>0:
                    self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], symbol=self.marketdata.tickernames[0],
                    assettype = obt.ASSET_TYPE_STOCK, action=obt.SELL_TO_OPEN, quantity = abs(deltadelta), ordertype=obt.ORDER_TYPE_MARKET))
                elif deltadelta<0:
                    self.outgoingorders.append(obt.Order(self.myid, tickerindex=0, ticker=self.marketdata.tickernames[0], symbol=self.marketdata.tickernames[0],
                    assettype = obt.ASSET_TYPE_STOCK, action=obt.BUY_TO_OPEN, quantity = abs(deltadelta), ordertype=obt.ORDER_TYPE_MARKET))

                check=1
                pass

            pass
        else:
            # We do not have a position, let us find one
            targetexpdate = optionsnapshot[(optionsnapshot['dte']>=45)].iloc[0]['expirationdate']
            allcalls = optionsnapshot[(optionsnapshot['pcflag']==1) & (optionsnapshot['expirationdate']==targetexpdate)]
            allputsz = optionsnapshot[(optionsnapshot['pcflag']==0) & (optionsnapshot['expirationdate']==targetexpdate)]
            allbothz = pd.merge(allcalls, allputsz, on='k')
            allbothz['totalvega'] = allbothz['vega_x'] + allbothz['vega_y']
            wheremaxvega = allbothz['totalvega'].idxmax()
            # let us short that SHIITTTTTT
            self.outgoingorders.append(obt.Order(self.myid, 0, self.marketdata.tickernames[0], obt.ASSET_TYPE_OPTION, allbothz.iloc[wheremaxvega]['symbol_x'],
                            obt.SELL_TO_OPEN, quantity=1, tickerprice=stockdata.iloc[-1]['close'], optionprice=allbothz.iloc[wheremaxvega]['bid_x'], 
                            ordertype=obt.ORDER_TYPE_MARKET, pcflag=1, k=allbothz.iloc[wheremaxvega]['k'], expirationdate=targetexpdate))
            self.outgoingorders.append(obt.Order(self.myid, 0, self.marketdata.tickernames[0], obt.ASSET_TYPE_OPTION, allbothz.iloc[wheremaxvega]['symbol_y'],
                            obt.SELL_TO_OPEN, quantity=1, tickerprice=stockdata.iloc[-1]['close'], optionprice=allbothz.iloc[wheremaxvega]['bid_y'], 
                            ordertype=obt.ORDER_TYPE_MARKET, pcflag=0, k=allbothz.iloc[wheremaxvega]['k'], expirationdate=targetexpdate))

            

        self.stockpositions.append(self.account.positions.getstockquantityforticker(self.marketdata.tickernames[0]))



        return self.outgoingorders


def main():
    """
        In this example, we have intraday data fro both the stock and the options. 
        However, the timestamps don't match. That's not a problem at all, and is a lot more realistic of algorithmic trading. The data arrives when it arrives.


        We will use the datetime from the stock data to run the show, i.e., set the chronology for Chronos

    """
    myaccount = [obt.Account(deposit=2000)]
    optiondta = pd.read_csv("./FOOintradayoption.csv", index_col=0)
    optiondta['symbol'] = optiondta['ticker'] + optiondta['pcflag'].astype(str) + optiondta['k'].astype(str) + optiondta['expirationdate']
    optiondta.sort_values(by=['datetime', 'pcflag', 'dte', 'k'], inplace=True)
    # optiondta['datetime2'] = pd.to_datetime(optiondta['datetime'].values, infer_datetime_format=True)
    # optiondta['datetime3'] = pd.to_datetime(optiondta['datetime'].values.astype(str), infer_datetime_format=True)
    optiondta['datetime'] = optiondta['datetime'].values.astype(str)
    optiondta['datetime'] = optiondta['datetime'].str.replace('-04:00','')
    optiondta['datetime'] = pd.to_datetime(optiondta['datetime'].values, infer_datetime_format=True)

    # optiondta.set_index('datetime', inplace=True)

    stockdata = pd.read_csv("./FOOintradaystock.csv", index_col=0)
    # stockdata['datetime'] = pd.to_datetime(stockdata['tdate'])
    # stockdata['datetime'] = stockdata['datetime'].dt.tz_localize('UTC').dt.tz_convert("US/Eastern")
    # stockdata['date_eod'] = stockdata['datetime'].dt.date
    # stockdata['justtimetofilter'] = stockdata['datetime'].dt.time
    # stockdata.drop(['total_volume', 'avg_trade_size', 'time_beg', 'vwap', 'opening_price', 'tick_vwap', 'time_end', 'save_date'], axis=1, inplace=True)
    # resample to 5min candles AAAANNNNNDDDDDD make the datetime column the index.
    # stockdata = stockdata.resample('10min', on='datetime').last().dropna()
    stockdata['datetime'] = pd.to_datetime(stockdata['timestamp'])
    stockdata['datetimeindex'] = stockdata['datetime']
    
    # stockdata.rename(columns={'timestamp':'datetime'}, inplace=True)
    # filterout pre and post market data
    stockdata.set_index('datetimeindex', inplace=True)
    stockdata = stockdata.between_time(datetime.time(8), datetime.time(15), include_start=True, include_end=True) 

    uniquetimesteps = pd.DataFrame(stockdata['datetime'].unique(), columns=['datetime'])
    uniquetimesteps['datetime'] = pd.to_datetime(uniquetimesteps['datetime'])

    tempcheckoptionfrequ = pd.DataFrame(optiondta['datetime'].unique(), columns=['datetime'])
    tempcheckoptionfrequ['datetime'] = pd.to_datetime(tempcheckoptionfrequ['datetime'])

    firstoptiondate = np.datetime64(tempcheckoptionfrequ.iloc[0]['datetime']).astype(datetime.datetime)
    wheretostart = uniquetimesteps.loc[uniquetimesteps['datetime']<firstoptiondate].index[-1]

    tickerSAMPLE = obt.OneTicker(tickername='FOO', tickertimeseries=stockdata, optionchaintimeseries=optiondta)
    
    mymarket = obt.Market([tickerSAMPLE],['FOO']) # <== When dealing with options, we need to have this match the ticker in the option data file
    mydealer = obt.Dealer(marketdata=mymarket)
    mystrategy = [MyStrategy(ratioRV_tohedge= 1, ratioPNL_takeprofit= .5, ratioPNL_takeloss= -0.5, ratioRV_takeloss= 0.5)]
    
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccount, clientstrategies=mystrategy, chronology=uniquetimesteps)

    mychronos.primingthestrategyat(wheretostart)

    # xstock, ystock = tickerSAMPLE.stocktimeseriestoplot()
    # plt.scatter(xstock, ystock, s=1)
    # plt.show()

    mychronos.execute()


    # fig, (ax1,ax2,ax3,ax4,ax5) = plt.subplots(5,1, sharex=False, sharey=False)
    fig, (ax1,ax2,ax3) = plt.subplots(3,1, sharex=False, sharey=False)
    ax1.plot(uniquetimesteps[-len(myaccount[0].totalvaluests):], myaccount[0].totalvaluests)
    ax1.yaxis.set_major_formatter('${x:1.2f}')
    ax1.set_title('Account value')
    ax2.scatter(uniquetimesteps[-len(myaccount[0].totalvaluests):],stockdata.iloc[-len(myaccount[0].totalvaluests):]['close'],s=1)
    ax2.yaxis.set_major_formatter('${x:1.2f}')
    ax2.legend()
    ax2.set_title('Stock Price')
    ax3.plot(uniquetimesteps[-len(mystrategy[0].stockpositions):], mystrategy[0].stockpositions)
    ax3.set_title('Stock positions')
    # ax4.plot(uniquetimesteps[-len(mystrategy.deltavalues):], mystrategy.deltavalues)
    # ax4.set_title('Delta values')
    # ax5.stem(mystrategy.buydates,1*np.ones(len(mystrategy.buydates),),linefmt='green')
    # ax5.stem(mystrategy.selldates,-1*np.ones(len(mystrategy.selldates),),linefmt='red')
    # ax4.set_title('Buy and sells of the put')
    fig.tight_layout()
    fig.suptitle('Short a 45+dte straddle, hedge if RV/IV > x, close position if ...{secret sauce}')
    plt.show()

    pausehere=1




if __name__ == '__main__':
    main()
