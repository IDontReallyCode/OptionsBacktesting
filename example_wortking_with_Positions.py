import optionbacktesting as obt
import pandas as pd

def main():
    mypositions = obt.Positions()

    print("Buy 10 shares at 10")
    print(mypositions.changestockposition('CLF', 10, 10))
    print("Buy 10 share at 5")
    print(mypositions.changestockposition('CLF', 1, 5))
    print("sell 1 share at 11")
    print(mypositions.changestockposition('CLF', -1, 11))
    print("Sell 10 shares at 15")
    print(mypositions.changestockposition('CLF', -10, 15))
    print("There should be 0 shares left in my positions")
    # print(mypositions.mypositions)

    print(mypositions.changeoptionposition('CLF', +1, 0.199, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions.changeoptionposition('CLF', +1, 1.188, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions.changeoptionposition('CLF', +1, 2.1077, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions.changeoptionposition('CLF', +1, 3.1066, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions.changeoptionposition('CLF', +1, 4.1055, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    # print(mypositions.mypositions)
    print(mypositions.changeoptionposition('CLF', -5, 3.34, 'CLF20221010040', 0, 40, pd.to_datetime('2022-10-10')))
    # print(mypositions.mypositions)

    print(mypositions.getoptionpositions('CLF'))

    print(mypositions.changeoptionposition('CLF', -3, 1.34, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions.changeoptionposition('CLF', -2, 1.34, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))

    print(mypositions.getoptionpositions('CLF'))
    print(mypositions.getoptionpositions('CLF','CLF20221010035'))

    print(mypositions.changeoptionposition('CLF', +3, 1.34, 'CLF20221010040', 0, 40, pd.to_datetime('2022-10-10')))
    print(mypositions.changeoptionposition('CLF', +2, 1.14, 'CLF20221010040', 0, 40, pd.to_datetime('2022-10-10')))

    print(mypositions.getoptionpositions('CLF'))

    done=1


if __name__ == '__main__':
    main()
