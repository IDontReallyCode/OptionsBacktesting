import numpy as np
import optionbacktesting as obt

def main():

    myaccount = obt.Account(deposit=5000, margintype=obt.MARGINTYPE_TDA)

    ordershortput = obt.Order(0, 'KSS', obt.ASSET_TYPE_OPTION, symbol='kssoptiontest', action=obt.SELL_TO_OPEN, quantity=1,
    tickerprice=32.68, optionprice=2.93, ordertype=obt.ORDER_TYPE_MARKET, pcflag=1, k=32.5, expirationdate='2022-09-16')

    margincalc = myaccount.estimatemargin(ordershortput)

    print(margincalc)
    print('close enough')

    ordershortcall = obt.Order(0, 'KSS', obt.ASSET_TYPE_OPTION, symbol='kssoptiontest', action=obt.SELL_TO_OPEN, quantity=1,
    tickerprice=32.68, optionprice=2.93, ordertype=obt.ORDER_TYPE_MARKET, pcflag=1, k=32.5, expirationdate='2022-09-16')

    margincalc = myaccount.estimatemargin(ordershortcall)

    print(margincalc)
    print('close enough')

    ordershortstock = obt.Order(0, 'KSS', obt.ASSET_TYPE_STOCK, symbol='kssoptiontest', action=obt.SELL_TO_OPEN, quantity=1,
    tickerprice=33.11, optionprice=0, ordertype=obt.ORDER_TYPE_MARKET)

    margincalc = myaccount.estimatemargin(ordershortstock)

    print(margincalc)
    print('close enough')


    pass
    
if __name__ == '__main__':
    main()
