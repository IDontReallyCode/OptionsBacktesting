import optionbacktesting as obt

def main():
    mypositions = obt.Positions()

    print(mypositions.getpositionofsymbol("CLF02022-05-07"))
    afterbuytoopen = mypositions.changeposition(+1, 0, "CLF02022-05-07", 1, 35, '2022-05-07')
    print(mypositions.getpositionofsymbol("CLF02022-05-07"))
    afterselltoclose = mypositions.changeposition(-1, 0, "CLF02022-05-07", 1, 35, '2022-05-07')
    print(mypositions.getpositionofsymbol("CLF02022-05-07"))
    afterbuytoopen = mypositions.changeposition(+1, 0, "CLF02022-05-07", 1, 35, '2022-05-07')
    print(mypositions.getpositionofsymbol("CLF02022-05-07"))
    afteraddingtoopenedpositions = mypositions.changeposition(+5, 0, "CLF02022-05-07", 1, 35, '2022-05-07')
    print(mypositions.getpositionofsymbol("CLF02022-05-07"))
    afteraddingnewpositions = mypositions.changeposition(+5, 0, "CLF02022-06-07", 1, 40, '2022-06-07')
    print(mypositions.getpositionsofticker(0))

    done=1


if __name__ == '__main__':
    main()
