import optionbacktesting as obt
import pandas as pd

def main():
    mypositions = obt.Positions()

    print("Buy 10 shares at 10")
    print(mypositions._changestockposition(0, 'RANDOMTICKER', 10, 10))
    print("Buy 10 share at 5")
    print(mypositions._changestockposition(0, 'RANDOMTICKER', 1, 5))
    print("sell 1 share at 11")
    print(mypositions._changestockposition(0, 'RANDOMTICKER', -1, 11))
    print("Sell 10 shares at 15")
    print(mypositions._changestockposition(0, 'RANDOMTICKER', -10, 15))
    print("There should be 0 shares left in my positions")
    # print(mypositions.mypositions)

    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +1, 0.199, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +1, 1.188, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +1, 2.1077, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +1, 3.1066, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +1, 4.1055, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    # print(mypositions.mypositions)
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', -5, 3.34, 'RANDOMTICKER20221010040', 0, 40, pd.to_datetime('2022-10-10')))
    # print(mypositions.mypositions)

    print(mypositions.getoptionpositions('RANDOMTICKER'))

    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', -3, 1.34, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', -2, 1.34, 'RANDOMTICKER20221010035', 0, 35, pd.to_datetime('2022-10-10')))

    print(mypositions.getoptionpositions('RANDOMTICKER'))
    print(mypositions.getoptionpositions('RANDOMTICKER','RANDOMTICKER20221010035'))

    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +3, 1.34, 'RANDOMTICKER20221010040', 0, 40, pd.to_datetime('2022-10-10')))
    print(mypositions._changeoptionposition(0, 'RANDOMTICKER', +2, 1.14, 'RANDOMTICKER20221010040', 0, 40, pd.to_datetime('2022-10-10')))

    print(mypositions.getoptionpositions('RANDOMTICKER'))

    done=1


if __name__ == '__main__':
    main()
