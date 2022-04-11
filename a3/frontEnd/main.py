# standard libraries
from datetime import datetime
import threading

# third party libraries
from flask import *
import numpy as np
from datetime import datetime
from datetime import timedelta
from dateutil import tz
from dateutil.relativedelta import relativedelta
import requests
import csv
import json
import numpy as np
import pandas as pd
import io
import os
import base64


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


@webapp.route('/stockRedirect', methods=['POST'])
def stockRedirect():
    """
    Get input client stock ticker fron ticker search bar and redirect to /stock/<ticker>
    Returns: Redirect to stock view page
    """
    stockTicker = request.form.get('stockTicker', "")

    if not stockTicker:  # If ticker is empty, raise error
        response = webapp.response_class(
            response=json.dumps("Ticker should not be empty."),
            status=400,
            mimetype='application/json'
        )
        print(response)
        return response

    # Under Construction
    # Add ticker not found later
    return redirect("/stock/" + str(stockTicker))


@webapp.route('/portfolioParse', methods=['GET', 'POST'])
def portfolioParse():
    """
    Get uploaded csv credential from client and parse it for edit
    Returns: Passing client credential to portfolioEditor page
    """
    # Parse csv file, pass info and redirect to portfolioEditor.html
    csvCredential = request.files['csvCredential']
    clientIP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    # If file not given, quit
    if csvCredential.filename == '': 
        response = webapp.response_class(
            response=json.dumps("Credential file not selected"),
            status=400,
            mimetype='application/json'
        )
        print(response)
        return response

    # Save credential file in S3 as cache
    if csvCredential:
        print(type(csvCredential))
        split_tup = os.path.splitext(csvCredential.filename)
        currentFileName = "credential_" + clientIP + split_tup[1]

        Config.s3.upload_public_inner_file(
            csvCredential, _object_name=currentFileName)
        print("Credential updated to S3 successfully")

    return redirect("/portfolioEditor/" + str(clientIP))


@webapp.route('/portfolioScratch', methods=['GET', 'POST'])
def portfolioScratch():
    """
    Create an empty csv credential for new client and pass it to portfolioEditor
    Returns: Passing empty credential to portfolioEditor page
    """
    clientIP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    # Create an empty credential for new client
    currentDate = datetime.date(datetime.now())
    header = {'Action':['Buy'], 'Ticker':[''], 'Amount':[''], 'Price':[''], 'Date':[currentDate], 'Comment':['<Comment Here>']}
    dfCredential = pd.DataFrame(header)
    print(dfCredential)
    emptyCredential = dfCredential.to_csv(sep=',', encoding='utf-8', index=False)

    # emptyCredential = [['Action','Ticker','Amount','Price','Date','Comment'],['','','','','','',]]
    # stream = io.StringIO()
    # csv.writer(stream).writerows(emptyCredential)

    # Save credential file in S3 as cache
    print(type(emptyCredential))
    currentFileName = "credential_" + clientIP + ".csv"

    Config.s3.upload_public_inner_file(
        emptyCredential, _object_name=currentFileName)
    print("Credential updated to S3 successfully")
    
    return redirect("/portfolioEditor/" + str(clientIP))


@webapp.route('/portfolioEditor/<clientIP>', methods=['GET', 'POST'])
def portfolioEditor(clientIP):
    """
    Get uploaded csv credential and remote ip from client and display for edit
    Returns: 'Portfolio Editor Page' html
    """
    # Get credential file from S3
    filename = "credential_" + clientIP + ".csv"
    file = base64.b64decode(Config.s3.get_file_in_base64(filename)).decode('utf-8')
    print("Credential downloaded from S3 successfully")

    # Parse and read csv
    stream = io.StringIO(file)
    readerCredential = csv.DictReader(stream, skipinitialspace=True)
    dictCredential = [{k: v for k, v in row.items()} for row in readerCredential]
    for row in dictCredential:
        print(row)
    # print(dictsCredential)

    return render_template("portfolioEditor.html", dictCredential = dictCredential, clientIP = clientIP)



@webapp.route('/stock/<ticker>')
def stock(ticker):
    """
    Stock Page
    Input:
     - ticker: str, 1-5 letter company name abbreviation
    Returns: stock.html of specific company rendered by flask
    """

    length = 390
    df, valid = Config.stockAPI.allQuote(ticker)

    if valid:
        closeData = df.loc[:, "close"]
        timeData = df.index
        volumeData = df.loc[:, "volume"]

        pricedata = closeData.to_list()
        xlabels = timeData.to_list()
        actiondata = volumeData.to_list()

        newXlabels = []

        for i in xlabels:
            newXlabels.append(i.strftime("%m/%d/%Y, %H:%M:%S"))

        lastDaynewXlabels = []
        lastDayPricedata = []
        lastDayActiondata = []

        lastWeekday = datetime.today() - timedelta(days=(0, 0, 0, 0,
                                                         0, 1, 2)[datetime.today().weekday()])
        if lastWeekday.strftime("%m/%d/%Y" + ", 09:30:00") in newXlabels:
            # trim list so that it only displays today's data
            trimIndex = newXlabels.index(
                lastWeekday.strftime("%m/%d/%Y" + ", 09:30:00"))

            lastDayNewXlabels = newXlabels[trimIndex:]
            lastDayPricedata = pricedata[trimIndex:]
            lastDayActiondata = actiondata[trimIndex:]

        fiveDaysNewXlabels = []
        fiveDaysPricedata = []
        fiveDaysActiondata = []

        fiveDaysEarlier = lastWeekday
        for i in range(4):
            fiveDaysEarlier = fiveDaysEarlier - timedelta(days=(3, 1, 1, 1,
                                                                1, 1, 2)[fiveDaysEarlier.weekday()])

        if fiveDaysEarlier.strftime("%m/%d/%Y" + ", 09:30:00") in newXlabels:
            trimIndex = newXlabels.index(
                fiveDaysEarlier.strftime("%m/%d/%Y" + ", 09:30:00"))

            fiveDaysNewXlabels = newXlabels[trimIndex:]
            fiveDaysPricedata = pricedata[trimIndex:]
            fiveDaysActiondata = actiondata[trimIndex:]

        tenDaysNewXlabels = []
        tenDaysPricedata = []
        tenDaysActiondata = []

        tenDaysEarlier = lastWeekday
        for i in range(9):
            tenDaysEarlier = tenDaysEarlier - timedelta(days=(3, 1, 1, 1,
                                                              1, 1, 2)[tenDaysEarlier.weekday()])

        if tenDaysEarlier.strftime("%m/%d/%Y" + ", 09:30:00") in newXlabels:
            trimIndex = newXlabels.index(
                tenDaysEarlier.strftime("%m/%d/%Y" + ", 09:30:00"))

            tenDaysNewXlabels = newXlabels[trimIndex:]
            tenDaysPricedata = pricedata[trimIndex:]
            tenDaysActiondata = actiondata[trimIndex:]

        currentPrice = pricedata[-1]

        chartName = "One Day View for " + ticker

        return render_template("stock.html",
                               xlabels=lastDayNewXlabels,
                               price=lastDayPricedata,
                               action=lastDayActiondata,
                               name=chartName
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
        redirect to main page
    """
    return redirect("/")


def createTestData(length=60):
    # ==================== Test data ========================
    pricedata = np.random.random(length)
    pricedata = (pricedata * 10).tolist()
    actiondata = np.random.random(length).tolist()
    xlabels = np.arange(length).tolist()
    # ==================== End Test ====================
    return pricedata, actiondata, xlabels


def makeAPI_Call(api_url: str, method: str, _timeout: int, _data={}):
    """Helper function to call an API.

    Args:
        api_url (str): URL to the API function
        method (str): get, post, delete, or put
        _timeout (int): (in seconds) how long should the front end wait for a response

    Returns:
        <?>: response
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1",
               "DNT": "1", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate"}
    method = method.lower()
    if method == "get":
        r = requests.get(api_url, timeout=_timeout, headers=headers)
    if method == "post":
        r = requests.post(api_url, data=_data,
                          timeout=_timeout, headers=headers)
    if method == "delete":
        r = requests.delete(api_url, timeout=_timeout, headers=headers)
    if method == "put":
        r = requests.put(api_url, timeout=_timeout, headers=headers)

    json_acceptable_string = r.json()

    return json_acceptable_string


def makeAPI_Call_Not_Json(api_url: str, method: str, _timeout: int, _data={}):
    """Helper function to call an API.

    Args:
        api_url (str): URL to the API function
        method (str): get, post, delete, or put
        _timeout (int): (in seconds) how long should the front end wait for a response

    Returns:
        <?>: response
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1",
               "DNT": "1", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate"}
    method = method.lower()
    if method == "get":
        r = requests.get(api_url, timeout=_timeout, headers=headers)
    if method == "post":
        r = requests.post(api_url, data=_data,
                          timeout=_timeout, headers=headers)
    if method == "delete":
        r = requests.delete(api_url, timeout=_timeout, headers=headers)
    if method == "put":
        r = requests.put(api_url, timeout=_timeout, headers=headers)

    return r
