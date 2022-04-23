# for imports see: https://blog.quantinsti.com/install-ta-lib-python/
import trading

def printHeader():
    print("##########################################################")
    print("########           EXECUTING PYTHON BOT           ########")
    print("##########################################################")
    print("##########################################################")
    print("\n")

def printFooter():
    print("\n")
    print("##########################################################")
    print("##########################################################")
    print("########            EXECUTING FINISHED            ########")
    print("##########################################################")

def main():
    printHeader()
    trading.checkPositions()
    printFooter()


main()