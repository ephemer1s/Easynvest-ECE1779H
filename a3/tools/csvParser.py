
import pandas as pd

import csv

try:
    from stockAPI import StockData
except ImportError:
    from tools.stockAPI import StockData


class StockAnalysisSuite(object):

    class StockAction(object):
        def __init__(self, _action=None, _ticker=None, _amount=None, _price=None, _date=None, _comment=None):
            self.action = _action  # Buy or Sell
            self.ticker = _ticker
            self.amount = _amount  # number of stock bought/sold
            self.price = _price  # price bought / sell stock at
            self.date = _date  # datetime.date.today().strftime("%Y-%m-%d")
            self.comment = ""
            if _comment != None:
                self.comment = _comment

    class StockPortfolioIndividual(object):
        def __init__(self, _ticker=None, _amount=None, _price=None, _currentPrice=None, _gain=None):
            self.ticker = _ticker
            self.amount = _amount  # number of stock owned
            self.avgPrice = _price  # Avg price bought stock at
            self.currentPrice = _currentPrice  # Price Right Now
            self.gain = _gain  # gain in percent (String)

    class StockPortfolio(object):
        def __init__(self):
            self.dict = {}
            self.actionList = []

        def __str__(self):

            returnString = "Ticker, Amount, AvgPrice, CurrentPrice, Gain"
            returnString = returnString + "\n"
            for key in self.dict:
                returnString = returnString+key + " " + str(self.dict[key].amount) + " " + str(
                    "{:6.2f}".format(self.dict[key].avgPrice)) + " " + str(self.dict[key].currentPrice) + " " + str(self.dict[key].gain) + "\n"

            returnString = returnString + "\n"

            returnString = returnString + "Action, Ticker, Amount, Price, Date, Comment"

            returnString = returnString + "\n"

            for stockAction in self.actionList:
                returnString = returnString + stockAction.action + " " + stockAction.ticker + " " + \
                    str(stockAction.amount) + " " + str(stockAction.price) + " " + \
                    str(stockAction.date) + " " + \
                    str(stockAction.comment) + "\n"

            return returnString

        def addAction(self, stockAction):
            self.actionList.append(stockAction)

        def deleteAction(self, _index):
            self.actionList.pop(_index)

        def modifyAction(self, _index, _action=None, _ticker=None, _amount=None, _price=None, _date=None, _comment=None):

            if _action != None:
                self.actionList[_index].action = _action  # Buy or Sell
            if _ticker != None:
                self.actionList[_index].ticker = _ticker
            if _amount != None:
                self.actionList[_index].amount = _amount
            if _price != None:
                self.actionList[_index].price = _price
            if _date != None:
                self.actionList[_index].date = _date
            if _comment != None:
                self.actionList[_index].comment = _comment

        def stopTracking(self, _ticker):
            """Remove all <ticker> stock from actionList and portfolio dict

            Args:
                _ticker (string): Ticker of Stock
            """

            for i in self.actionList:
                if i.ticker == _ticker:
                    self.actionList.remove(i)

            self.dict.pop(_ticker, "Stock Removed")

        def clearAll(self):
            self.dict = {}
            self.actionList = []

        def readFromCSV(self, filename):
            self.dict = {}
            self.actionList = []
            df = pd.read_csv(filename, header=[0])
            if list(df) != ["Action", "Ticker", "Amount", "Price", "Date", "Comment"]:
                print("Wrong Format.", list(
                    df), ", should be [\"Action\",\"Ticker\", \"Amount\", \"Price\", \"Date\", \"Comment\"]")
                return False
            for i in df.itertuples():
                comment = ""

                if str(i.Comment) == "nan":
                    comment = ""
                else:
                    comment = i.Comment

                self.actionList.append(StockAnalysisSuite.StockAction(
                    _action=i.Action, _ticker=i.Ticker, _amount=int(i.Amount), _price=float(i.Price), _date=i.Date, _comment=comment))

            self.compilePortfolio()

        def addFromCSV(self, filename):
            self.dict = {}
            df = pd.read_csv(filename, header=[0])
            if list(df) != ["Action", "Ticker", "Amount", "Price", "Date", "Comment"]:
                print("Wrong Format.", list(
                    df), ", should be [\"Action\",\"Ticker\", \"Amount\", \"Price\", \"Date\", \"Comment\"]")
                return False
            for i in df.itertuples():
                comment = ""

                if str(i.Comment) == "nan":
                    comment = ""
                else:
                    comment = i.Comment

                self.actionList.append(StockAnalysisSuite.StockAction(
                    _action=i.Action, _ticker=i.Ticker, _amount=int(i.Amount), _price=float(i.Price), _date=i.Date, _comment=comment))
            self.compilePortfolio()

        def compilePortfolio(self):
            self.dict = {}
            for stockAction in self.actionList:
                if stockAction.ticker not in self.dict.keys():
                    if stockAction.action == "Buy":
                        self.dict[stockAction.ticker] = StockAnalysisSuite.StockPortfolioIndividual(
                            _ticker=stockAction.ticker, _amount=stockAction.amount, _price=stockAction.price)
                    elif stockAction.action == "Sell":
                        self.dict[stockAction.ticker] = StockAnalysisSuite.StockPortfolioIndividual(
                            _ticker=stockAction.ticker, _amount=0, _price=0)
                else:
                    oldAmount = self.dict[stockAction.ticker].amount
                    oldPrice = self.dict[stockAction.ticker].avgPrice

                    addedAmount = stockAction.amount
                    addedPrice = stockAction.price

                    if stockAction.action == "Buy":

                        newAmount = oldAmount + addedAmount
                        totalPrice = oldAmount * oldPrice + addedAmount * addedPrice

                        if newAmount == 0:
                            newAvgPrice = 0
                        else:
                            newAvgPrice = totalPrice / float(newAmount)

                    elif stockAction.action == "Sell":
                        newAmount = oldAmount - addedAmount

                        if newAmount < 0:
                            newAmount = 0
                            newAvgPrice = 0
                            totalPrice = 0
                        else:
                            totalPrice = newAmount * oldPrice
                            newAvgPrice = oldPrice

                    self.dict[stockAction.ticker].avgPrice = newAvgPrice
                    self.dict[stockAction.ticker].amount = newAmount

        def updateGain(self):

            listOfTickers = list(self.dict.keys())
            stockAPI = StockData()
            liveQuotes, validBool = stockAPI.liveQuotes(listOfTickers)

            if validBool:
                indexIter = 0

                for i in self.dict:
                    self.dict[i].currentPrice = float(liveQuotes[indexIter])
                    indexIter = indexIter + 1

                    if self.dict[i].avgPrice != 0:
                        self.dict[i].gain = str(
                            ("{:6.2f}".format(((self.dict[i].currentPrice - self.dict[i].avgPrice) / self.dict[i].avgPrice) * 100))) + "%"
                    else:
                        self.dict[i].gain = "N/A"
            else:
                print("Invalid ticker(s) entered.")

        def exportCSV(self, filename):
            # open the file in the write mode
            f = open(filename, 'w')

            # create the csv writer
            writer = csv.writer(f)

            writer.writerow(["Action", "Ticker", "Amount",
                             "Price", "Date", "Comment"])

            # write a row to the csv file

            for stockAction in self.actionList:
                row = [stockAction.action, stockAction.ticker, str(stockAction.amount), str(
                    stockAction.price), str(stockAction.date), str(stockAction.comment)]
                writer.writerow(row)

            # close the file
            f.close()


# TESTING -----------------------------
if __name__ == '__main__':
    stockAnalysisSuiteObject = StockAnalysisSuite()
    myPortfolio = stockAnalysisSuiteObject.StockPortfolio()
    myPortfolio.readFromCSV("Sheet1.csv")
    myPortfolio.compilePortfolio()
    myPortfolio.updateGain()

    print(myPortfolio)
    myPortfolio.exportCSV("MyPortfolio1.csv")

    myPortfolio.readFromCSV("MyPortfolio1.csv")
    myPortfolio.deleteAction(1)
    myPortfolio.stopTracking("V")

    myPortfolio.modifyAction(3, _amount=120, _comment="BIG CHUNGUS")
    myPortfolio.compilePortfolio()
    myPortfolio.updateGain()
    print(myPortfolio)
    myPortfolio.exportCSV("MyPortfolio2.csv")
