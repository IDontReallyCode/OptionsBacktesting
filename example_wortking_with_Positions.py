import optionbacktesting as obt
import pandas as pd

def main():
    mypositions = obt.Positions()

    print(mypositions.changestockposition('CLF', 10))
    # print(mypositions.mypositions)

    print(mypositions.changeoptionposition('CLF', +5, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))
    # print(mypositions.mypositions)
    print(mypositions.changeoptionposition('CLF', -5, 'CLF20221010040', 0, 40, pd.to_datetime('2022-10-10')))
    # print(mypositions.mypositions)

    print(mypositions.getoptionpositions('CLF'))

    print(mypositions.changeoptionposition('CLF', -5, 'CLF20221010035', 0, 35, pd.to_datetime('2022-10-10')))

    print(mypositions.getoptionpositions('CLF'))
    print(mypositions.getoptionpositions('CLF','CLF20221010035'))

    print(mypositions.changeoptionposition('CLF', +5, 'CLF20221010040', 0, 40, pd.to_datetime('2022-10-10')))

    print(mypositions.getoptionpositions('CLF'))

    done=1


if __name__ == '__main__':
    main()
