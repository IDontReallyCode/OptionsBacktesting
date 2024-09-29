"""
    This is a basic example:

    Strategy:
        We assume the strategy comes from another program, and we are just implementing it here.
        We assume the strategy does not have a look-ahead bias, and it is not using any future data.
        The strategy contains buy and sell orders for an option strategy that intends to make profits out of a SMILE increase of decrease.
        
"""

# from calendar import weekday
import numpy as np
import pandas as pd
# from pyparsing import col
import optionbacktesting as obt
# import datetime
import matplotlib.pyplot as plt
import matplotlib.axes as axes



class MyStrategy(obt.abstractstrategy.Strategy):

    def __init__(self, strategydataframe) -> None:
        super().__init__()
        self.buydates = []
        self.selldates = []
        self.stockpositions = []
        self.deltavalues = []
        self.strategy = strategydataframe

    def estimatestrategy(self, marketfeedback, accountfeedback):
        super().estimatestrategy(marketfeedback, accountfeedback)


        currentoptionpositions = self.account.positions.getoptionpositions(self.marketdata.tickernames[0])

        strategy_today: pd.DataFrame
        if not currentoptionpositions:
            current_date = self.marketdata.currentdatetime
            current_date = current_date.strftime('%Y-%m-%d')
            strategy_today = self.strategy[self.strategy['datetime'] == current_date]

            if strategy_today['signal'].values[0] in [1, -1]:
                optionsnapshot = self.marketdata.tickerlist[0].getoptionsnapshot().copy()
                stockdata = self.marketdata.tickerlist[0].getstockdata()
                # get the value of the stock price on last day avaliable in data
                spot = stockdata['close'].iloc[-1]
                # get the ATM strike that is the closest to the spot price
                # to do that, we calculate the difference between the strike and the spot price
                # and we get the strike with the smallest difference
                # optionsnapshot = optionsnapshot.copy()
                optionsnapshot.loc[:, 'k_diff'] = np.abs(optionsnapshot['k'] - spot)
                ATM_strike = optionsnapshot.loc[optionsnapshot['k_diff'].idxmin(), 'k']
                # keep only the rows where 'k'==ATM_strike
                ATM_options = optionsnapshot.loc[optionsnapshot['k'] == ATM_strike]
                # get the rows with smallest dte, where dte>5
                ATM_options = ATM_options[ATM_options['dte'] > 5]
                ATM_options = ATM_options[ATM_options['dte'] == ATM_options['dte'].min()]
                # Get the call
                call = ATM_options[ATM_options['pcflag'] == 1]
                # Get the put
                put = ATM_options[ATM_options['pcflag'] == 0]
                
                # now for the wings, we filter out bid<0.01
                liquidoptions = optionsnapshot.loc[optionsnapshot['bid']>0.00]
                liquidoptions = liquidoptions.loc[liquidoptions['dte']>6]
                # now keep only those with 'dte' with the smallest value, and keep them all with smallest value of dte
                liquidoptions = liquidoptions[liquidoptions['dte'] == liquidoptions['dte'].min()]
                # keep only those with 'OI' > 0
                liquidoptions = liquidoptions[liquidoptions['openinterest'] > 0]
                # keep only those with 'volume > 0
                liquidoptions = liquidoptions[liquidoptions['volume'] > 0]
                wingcalls = liquidoptions[liquidoptions['pcflag'] == 1]
                wingputs = liquidoptions[liquidoptions['pcflag'] == 0]
                # now, wingouts and wingcalls have a 'k_diff'.
                # I want to know what is the largest k_diff that is in both wingcalls and wingputs
                common_k_diff = np.intersect1d(wingcalls['k_diff'], wingputs['k_diff'])
                if len(common_k_diff) > 0:
                    largest_common_k_diff = common_k_diff.max()
                    wingcall = wingcalls[wingcalls['k_diff'] == largest_common_k_diff].iloc[0]
                    wingput = wingputs[wingputs['k_diff'] == largest_common_k_diff].iloc[0]
                else:
                    wingcall = wingcalls.iloc[0]
                    wingput = wingputs.iloc[0]


            if strategy_today['signal'].values[0] == 1:
                # CREATE AN ORDER for the call
                order_call_body = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=call.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= call.iloc[0]['symbol'], 
                                        action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=call.iloc[0]['pcflag'], 
                                        k=call.iloc[0]['k'], expirationdate=call.iloc[0]['expirationdate'])
                # CREATE AN ORDER for the put
                order_put__body = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=put.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= put.iloc[0]['symbol'], 
                                        action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=put.iloc[0]['pcflag'], 
                                        k=put.iloc[0]['k'], expirationdate=put.iloc[0]['expirationdate'])
                
                # CREATE AN ORDER for the call
                order_call_wing = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=call.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= wingcall.iloc[0]['symbol'], 
                                        action=obt.SELL_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=wingcall.iloc[0]['pcflag'], 
                                        k=wingcall.iloc[0]['k'], expirationdate=wingcall.iloc[0]['expirationdate'])
                # CREATE AN ORDER for the put
                order_put__wing = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=put.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= wingput.iloc[0]['symbol'], 
                                        action=obt.SELL_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=wingput.iloc[0]['pcflag'], 
                                        k=wingput.iloc[0]['k'], expirationdate=wingput.iloc[0]['expirationdate'])
                
                self.outgoingorders.append(order_call_body)
                self.outgoingorders.append(order_put__body)
                self.outgoingorders.append(order_call_wing)
                self.outgoingorders.append(order_put__wing)                # we buy the butterfly
                pausehere = 1
                
            elif strategy_today['signal'].values[0] == -1:
                # CREATE AN ORDER for the call
                order_call_body = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=call.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= call.iloc[0]['symbol'], 
                                        action=obt.SELL_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=call.iloc[0]['pcflag'], 
                                        k=call.iloc[0]['k'], expirationdate=call.iloc[0]['expirationdate'])
                # CREATE AN ORDER for the put
                order_put__body = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=put.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= put.iloc[0]['symbol'], 
                                        action=obt.SELL_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=put.iloc[0]['pcflag'], 
                                        k=put.iloc[0]['k'], expirationdate=put.iloc[0]['expirationdate'])
                
                # CREATE AN ORDER for the call
                order_call_wing = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=call.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= wingcall.iloc[0]['symbol'], 
                                        action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=wingcall.iloc[0]['pcflag'], 
                                        k=wingcall.iloc[0]['k'], expirationdate=wingcall.iloc[0]['expirationdate'])
                # CREATE AN ORDER for the put
                order_put__wing = obt.Order(strategyid=self.myid, tickerindex = 0, ticker=put.iloc[0]['ticker'], assettype=obt.ASSET_TYPE_OPTION, symbol= wingput.iloc[0]['symbol'], 
                                        action=obt.BUY_TO_OPEN, quantity=+1, ordertype=obt.ORDER_TYPE_MARKET, pcflag=wingput.iloc[0]['pcflag'], 
                                        k=wingput.iloc[0]['k'], expirationdate=wingput.iloc[0]['expirationdate'])
                
                self.outgoingorders.append(order_call_body)
                self.outgoingorders.append(order_put__body)
                self.outgoingorders.append(order_call_wing)
                self.outgoingorders.append(order_put__wing)
                pausehere = 1
            else:
                pass

        return self.outgoingorders




def main():
    myaccount = [obt.Account(deposit=2000)]
    optiondta = pd.read_csv("./SAMPLEdailyoption.csv", index_col=0)
    stockdata = pd.read_csv("./SAMPLEdailystock.csv", index_col=0)
    stockdata['datetime'] = pd.to_datetime(stockdata['date_eod'])
    # TODO  when creating the datetime column, it needs to be a datetime format.
    optiondta['datetime'] = pd.to_datetime(optiondta['date_eod']) # required column
    optiondta.rename(columns={'oi':'openinterest', 'date_mat':'expirationdate'}, inplace=True)
    optiondta['symbol'] = optiondta['ticker'] + optiondta['pcflag'].astype(str) + optiondta['k'].astype(str) + optiondta['expirationdate']
    uniquedaydates = pd.DataFrame(optiondta['date_eod'].unique(), columns=['datetime'])
    uniquedaydates['datetime'] = pd.to_datetime(uniquedaydates['datetime'])

    tickerSAMPLE = obt.OneTicker(tickername='SAMPLE', tickertimeseries=stockdata, optionchaintimeseries=optiondta)
    strategy_data = pd.read_csv("./SAMPLEfakebutterflytrades.csv")
    
    mymarket = obt.Market([tickerSAMPLE],['SAMPLE']) # <== When dealing with options, we need to have this match the ticker in the option data file
    # mydealer = obt.Dealer(marketdata=mymarket, optiontradeprice=obt.TRAD_METH_OPTN_WCS)
    # mydealer = obt.Dealer(marketdata=mymarket, optiontradeprice=obt.TRAD_METH_OPTN_BCS)
    # mydealer = obt.Dealer(marketdata=mymarket, optiontradeprice=obt.TRAD_METH_OPTN_25P)
    # mydealer = obt.Dealer(marketdata=mymarket, optiontradeprice=obt.TRAD_METH_OPTN_MID)
    # mydealer = obt.Dealer(marketdata=mymarket, optiontradeprice=obt.TRAD_METH_OPTN_75P)
    mydealer = obt.Dealer(marketdata=mymarket, optiontradeprice=obt.TRAD_METH_OPTN_RND)
    mystrategy = [MyStrategy(strategy_data)]
    mychronos = obt.Chronos(marketdata=mymarket, marketdealer=mydealer, clientaccounts=myaccount, clientstrategies=mystrategy, chronology=uniquedaydates)

    mychronos.primingthestrategyat(1)

    mychronos.execute()


    ax1: axes._axes.Axes
    ax2: axes._axes.Axes
    ax3: axes._axes.Axes
    ax4: axes._axes.Axes
    ax5: axes._axes.Axes
    fig, (ax1,ax2,ax3,ax4,ax5) = plt.subplots(5,1, sharex=False, sharey=False)
    ax1.plot(uniquedaydates[-len(myaccount[0].totalvaluests):], myaccount[0].totalvaluests)
    ax1.yaxis.set_major_formatter('${x:1.2f}')
    ax1.set_title('Account value')
    ax2.plot(uniquedaydates[-len(myaccount[0].totalvaluests):],stockdata.iloc[-len(myaccount[0].totalvaluests):]['close'],label='close')
    ax2.yaxis.set_major_formatter('${x:1.2f}')
    ax2.legend()
    ax2.set_title('Stock Price')
    ax3.plot(uniquedaydates[-len(mystrategy[0].stockpositions):], mystrategy[0].stockpositions)
    ax3.set_title('Stock positions')
    ax4.plot(uniquedaydates[-len(mystrategy[0].deltavalues):], mystrategy[0].deltavalues)
    ax4.set_title('Delta values')
    ax5.stem(mystrategy[0].buydates,1*np.ones(len(mystrategy[0].buydates),),linefmt='green')
    ax5.stem(mystrategy[0].selldates,-1*np.ones(len(mystrategy[0].selldates),),linefmt='red')
    ax5.set_title('Buy and sells of the put')
    fig.tight_layout()
    fig.suptitle('Buy a put on Monday, Delta hedge it all week, close position on Friday')
    plt.show()


    
    print('all orders submitted')
    print(pd.DataFrame(mydealer.orderlistall))
    # [TODO] have the action print as BUY or SELL instead of 1 or -1

    print('\nall orders executed')
    print(pd.DataFrame(mydealer.orderlistexecuted))



    pausehere=1




if __name__ == '__main__':
    main()
