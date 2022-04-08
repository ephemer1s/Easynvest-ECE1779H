# standard libraries
from datetime import datetime
import threading

# third party libraries
from flask import *
import numpy as np
from datetime import datetime
from dateutil import tz
from dateutil.relativedelta import relativedelta


# local import
from frontEnd import webapp
from frontEnd.config import Config
from frontEnd.charts import Chart


@webapp.route('/')
def index():
    """
    Main Page
    Returns: 'Main Page' rendered by flask
    """
    # Under Construction
    # Need to fill price & value before deployment
    nasdaqCurrentPrice = 182
    nasdaqCurrentInterest = -0.18
    return render_template("mainpage.html", nasdaqCurrentPrice = nasdaqCurrentPrice, nasdaqCurrentInterest = nasdaqCurrentInterest)

@webapp.route('/portfolio')
def portfolio():
    """
    Portfolio Page
    Returns: 'Portfolio Page' html
    """
    return render_template("portfolioLogin.html")


@webapp.route('/stockRedirect')
def stockRedirect():
    """
    Get input client stock ticker fron ticker search bar and redirect to /stock/<ticker>
    """
    stockTicker = request.form.get('stockTicker', "")

    # Under Construction
    # localhostIP = urllib.request.urlopen("http://169.254.169.254/latest/meta-data/public-ipv4").read().decode('UTF-8')
    # Not functionable right now (?)
    return redirect("http://" + "127.0.0.1" + ":5000/stock/" + stockTicker)


@webapp.route('/portfolioParse')
def portfolioParse():
    """
    Get uploaded csv credential from client and parse it for edit
    """

    # Under Construction
    # Parse csv file, pass info and redirect to portfolioEditor.html
    return render_template("portfolioEditor.html")


@webapp.route('/portfolioEditor')
def portfolioEditor():
    """
    Get uploaded csv credential from client and display for edit
    Returns: 'Portfolio Editor Page' html
    """

    # Under Construction
    return render_template("portfolioEditor.html")

@webapp.route('/stock/<ticker>')
def stock(ticker):
    """
    Stock Page
    Input:
     - ticker: str, 3-5 letter company name abbreviation
    Returns: stock.html of specific company rendered by flask
    """

    length = 390
    df, valid = Config.stockAPI.dailyQuote(ticker)

    if valid:
        closeData = df.loc[:, "close"]
        timeData = df.index
        volumeData = df.loc[:, "volume"]

        pricedata = closeData.to_list()
        xlabels = timeData.to_list()
        actiondata = volumeData.to_list()

        return render_template("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               )
    else:  # ticker DNE
        pricedata, actiondata, xlabels = createTestData()
        print("using test data")
        return render_template("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               )


@webapp.route('/stock', methods=['POST'])
def browseStock():
    """
    Stock Page
    Same as @webapp.route('/stock/<ticker>'), but different method
    """
    ticker = request.form.get('key')
    length = 390
    df, valid = Config.stockAPI.dailyQuote(ticker)

    if valid:
        closeData = df.loc[:, "close"]
        timeData = df.index
        volumeData = df.loc[:, "volume"]

        pricedata = closeData.to_list()
        xlabels = timeData.to_list()
        actiondata = volumeData.to_list()

        return render_template("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               )
    else:  # ticker DNE
        # ==================== Test data ========================
        length = 60
        pricedata = np.random.random(length)
        pricedata = (pricedata * 10).tolist()
        actiondata = np.random.random(length).tolist()
        xlabels = np.arange(length).tolist()
        # ==================== End Test ====================
        return render_template("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               )

@webapp.route('/home')
def home():
    """Home Page: Call to go back to main page "/"

    Returns:
        html of Main Page
    """
    return render_template("mainpage.html")


def createTestData(length=60):
        # ==================== Test data ========================
        pricedata = np.random.random(length)
        pricedata = (pricedata * 10).tolist()
        actiondata = np.random.random(length).tolist()
        xlabels = np.arange(length).tolist()
        # ==================== End Test ====================
        return pricedata, actiondata, xlabels