# lambda-apigw.py --
# used for render templates without flask application
# author: ephemer1s

import base64
import csv
import io
import json
import os
from datetime import datetime, timedelta
import jinja2
import numpy as np
import pandas as pd
# from flask import *  # ephemer1s: if there is no web app, you should not import flask.
import requests
from frontEnd.backEnd import loadLogo
from frontEnd.config import Config


def render_template_without_flask(template_name, **template_vars):
    """
    Usage is the same as flask.render_template:
    render_template('my_template.html', var1='foo', var2='bar')
    """
    if os.path.exists('./frontEnd/lamplates'):
        template_path = './frontEnd/lamplates'
    else:
        template_path = './lamplates'

    templateLoader = jinja2.FileSystemLoader(searchpath=template_path)
    env = jinja2.Environment(loader=templateLoader)

    template = env.get_template(template_name)
    return template.render(**template_vars)


def wrap(body):
    '''
    Wrap the rendered template in a http response with status code 200
    '''
    return {
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html'},
        "body": body
    }


# @webapp.route('/home')
def index(event, context):
    """Home Page: Call to go back to main page "/"

    Returns:
        html of Main Page
    """
    logoContent_GSPC, logoExtension_GSPC, lastDayNewXlabels_GSPC, lastDayPricedata_GSPC, lastDayActiondata_GSPC, currentPrice_GSPC, currentGain_GSPC = stockChartLastDay("GSPC")

    return wrap(render_template_without_flask("mainpage.html",
                            name_GSPC = "S&P 500 Index (GSPC)",
                            logoContent_GSPC = logoContent_GSPC,
                            logoExtension_GSPC = logoExtension_GSPC,
                            lastDayNewXlabels_GSPC = lastDayNewXlabels_GSPC,
                            lastDayPrice_GSPC = lastDayPricedata_GSPC,
                            lastDayAction_GSPC = lastDayActiondata_GSPC,
                            currentPrice_GSPC = currentPrice_GSPC,
                            currentGain_GSPC = currentGain_GSPC))


def home(event, context):
    """Home Page: Call to go back to main page "/"

    Returns:
        redirect to main page
    """
    return index(event, context)


def stockChartLastDay(ticker):
    """ Get the necessary info for displaying last day stock chart more easily

    Returns:
        stock logo image, chart labels, last day price, last day action 
    """

    # Get stock logo image
    logoContent = None
    logoExtension = None
    logoBase64FormatImage, logoValidBool = loadLogo(ticker)
    if logoValidBool:
        logoContent = logoBase64FormatImage
        logoExtension = ".png"

    # Get stock data for chart
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

        lastDayNewXlabels = []
        lastDayPricedata = []
        lastDayActiondata = []

        lastWeekday = datetime.today() - timedelta(days=(0, 0, 0, 0,
                                                         0, 1, 2)[datetime.today().weekday()])

        while lastWeekday.strftime("%m/%d/%Y" + ", 09:30:00") not in newXlabels:
            lastWeekday = lastWeekday - timedelta(days=(1, 1, 1, 1,
                                                         1, 1, 2)[lastWeekday.weekday()])

        if lastWeekday.strftime("%m/%d/%Y" + ", 09:30:00") in newXlabels:
            # trim list so that it only displays today's data
            trimIndex = newXlabels.index(
                lastWeekday.strftime("%m/%d/%Y" + ", 09:30:00"))

            lastDayNewXlabels = newXlabels[trimIndex:]
            lastDayPricedata = pricedata[trimIndex:]
            lastDayActiondata = actiondata[trimIndex:]

        # Get current price and calculate current gain
        currentPrice = pricedata[-1]

        lastCloseWeekday = datetime.today() - timedelta(days=(3, 1, 1, 1,
                                                              1, 1, 2)[datetime.today().weekday()])

        if lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00") in newXlabels:
            trimIndex = newXlabels.index(
                lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00"))

        if pricedata[trimIndex] == currentPrice:
            lastCloseWeekday = lastCloseWeekday - timedelta(days=(1, 1, 1, 1,
                                                            1, 1, 1)[lastCloseWeekday.weekday()])
            if lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00") in newXlabels:
                trimIndex = newXlabels.index(
                    lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00"))

        yesterdayClosePrice = pricedata[trimIndex]
                               
        currentGain = round(100 * currentPrice / yesterdayClosePrice - 100, 2)
        
        return logoContent, logoExtension, lastDayNewXlabels, lastDayPricedata, lastDayActiondata, currentPrice, currentGain


# @webapp.route('/portfolio')
def portfolio(event, context):
    """
    Portfolio Page
    Returns: 'Portfolio Page' html
    """
    return wrap(render_template_without_flask("portfolioLogin.html"))


# @webapp.route('/stockRedirect', methods=['POST'])
def stockRedirect(event, context):
    """
    Get input client stock ticker fron ticker search bar and redirect to /stock/<ticker>
    """
    print(event['body'])
    body_raw = str(event['body'])
    tmp = body_raw.split('form-data; name=\"stockTicker\"\r\n\r\n')[1]
    stockTicker = tmp.split('\r\n-')[0]
    print('stockTicker ID : {}'.format(stockTicker))
    html_rendered = stock(stockTicker)
    return html_rendered



# @webapp.route('/stock/<ticker>')
# this is not a handler!
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

        lastDayNewXlabels = []
        lastDayPricedata = []
        lastDayActiondata = []

        lastWeekday = datetime.today() - timedelta(days=(0, 0, 0, 0,
                                                         0, 1, 2)[datetime.today().weekday()])

        while lastWeekday.strftime("%m/%d/%Y" + ", 09:30:00") not in newXlabels:
            lastWeekday = lastWeekday - timedelta(days=(1, 1, 1, 1,
                                                         1, 1, 2)[lastWeekday.weekday()])

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


        # Get current price and calculate current gain
        currentPrice = pricedata[-1]

        lastCloseWeekday = datetime.today() - timedelta(days=(3, 1, 1, 1,
                                                              1, 1, 2)[datetime.today().weekday()])

        if lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00") in newXlabels:
            trimIndex = newXlabels.index(
                lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00"))

        if pricedata[trimIndex] == currentPrice:
            lastCloseWeekday = lastCloseWeekday - timedelta(days=(1, 1, 1, 1,
                                                            1, 1, 1)[lastCloseWeekday.weekday()])
            if lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00") in newXlabels:
                trimIndex = newXlabels.index(
                    lastCloseWeekday.strftime("%m/%d/%Y" + ", 15:59:00"))

        yesterdayClosePrice = pricedata[trimIndex]
                               
        currentGain = round(100 * currentPrice / yesterdayClosePrice - 100, 2)
        chartName = "Stock View for " + ticker

        # Get stock logo image
        logoContent = None
        logoExtension = None
        logoBase64FormatImage, logoValidBool = loadLogo(ticker)
        if logoValidBool:
            logoContent = logoBase64FormatImage
            logoExtension = ".png"

        return wrap(render_template_without_flask("stock.html",
                               stockTicker=ticker,

                               logoContent = logoContent,
                               logoExtension = logoExtension,

                               lastDayNewXlabels=lastDayNewXlabels,
                               lastDayPrice=lastDayPricedata,
                               lastDayAction=lastDayActiondata,

                               fiveDaysNewXlabels=fiveDaysNewXlabels,
                               fiveDaysPrice=fiveDaysPricedata,
                               fiveDaysAction=fiveDaysActiondata,

                               tenDaysNewXlabels=tenDaysNewXlabels,
                               tenDaysPrice=tenDaysPricedata,
                               tenDaysAction=tenDaysActiondata,

                               name=chartName,
                               stockCurrentPrice=currentPrice,
                               stockCurrentGain=currentGain
                               ))
    # If use input an invalid ticker
    else:  
        # test data: ticker DNE
        # pricedata, actiondata, xlabels = createTestData()
        # print("using test data")
        # return render_template("stock.html",
        #                        xlabels=xlabels,
        #                        price=pricedata,
        #                        action=actiondata,
        #                        name=ticker
        #                        )
        return wrap(render_template_without_flask("invalidTicker.html"))


# @webapp.route('/portfolioParse', methods=['GET', 'POST'])
def portfolioParse(event, context):
    """
    Get uploaded csv credential from client and parse it for edit
    Returns: Passing client credential to portfolioEditor page
    """
    # Parse csv file, pass info and redirect to portfolioEditor.html
    #TODO @ ephemer1s
    # csvCredential = request.files['csvCredential']
    # clientIP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    csvCredential = event['csvCredential']
    clientIP = event['requestContext']['identity']['sourceIp']
    # If file not given, quit
    if csvCredential.filename == '': 
        # response = webapp.response_class(
        #     response=json.dumps("Credential file not selected"),
        #     status=400,
        #     mimetype='application/json'
        # )
        response = {
            "statusCode": 400,
            "headers": {'Content-Type': 'application/json'},
            "body": 'Credential file not selected'
        }
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
    # return redirect("/portfolioEditor/" + str(clientIP))
    return portfolioEditor(str(clientIP))


# @webapp.route('/portfolioScratch', methods=['GET', 'POST'])
def portfolioScratch(event, context):
    """
    Create an empty csv credential for new client and pass it to portfolioEditor
    Returns: Passing empty credential to portfolioEditor page
    """
    #TODO @ ephemer1s
    # clientIP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    clientIP = event['requestContext']['identity']['sourceIp']
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
    # return redirect("/portfolioEditor/" + str(clientIP))
    return portfolioEditor(str(clientIP))


# @webapp.route('/portfolioEditor/<clientIP>', methods=['GET', 'POST'])
# this is not a handler!
def portfolioEditor(clientIP):
    """
    Get uploaded csv credential and remote ip from client and display for edit
    Returns: 'Portfolio Editor Page' html
    """
    # Get credential file from S3
    filename = "credential_" + clientIP + ".csv"
    file = base64.b64decode(Config.s3.get_file_in_base64(filename)).decode('utf-8')
    print("Credential downloaded from S3 successfully")

    # Parse and read csv for table editor
    stream = io.StringIO(file)
    readerCredential = csv.DictReader(stream, skipinitialspace=True)
    dictCredential = [{k: v for k, v in row.items()} for row in readerCredential]

    # Group stock by ticker for portfolio info table
    stockList = []
    portfolioGain = []

    # When user uploaded a not empty credential
    if not dictCredential[0]['Ticker'] == '':
        for row in dictCredential:
            # print(row)
            ticker = row['Ticker']

            # If ticker already exists in the stock table (early record) and late record of the same ticker were found
            if ticker in stockList:
                if row['Action'] == 'Buy':
                    for stock in portfolioGain:
                        if stock['Ticker'] == ticker:
                            stock['BuyInPrice'] = (stock['Amount'] * stock['BuyInPrice'] + int(row['Amount']) * float(row['Price']))/(stock['Amount'] + int(row['Amount']))
                            stock['Amount'] += int(row['Amount'])
                elif row['Action'] == 'Sell':
                    for stock in portfolioGain:
                        if stock['Ticker'] == ticker:
                            # Check if stock amount after selling still >= 0 --> No negative stock amount is allowed
                            # if (stock['Amount'] - int(row['Amount'])) >= 0:
                                stock['Amount'] -= int(row['Amount'])
                            # else:
                            #     response = webapp.response_class(
                            #     response=json.dumps("Credential file contains negative stock amount. Please check again."),
                            #     status=400,
                            #     mimetype='application/json'
                            #     )
                            #     print(response)
                            #     return response
            else:
                # User could not sell a stock without buying in before
                # if row['Action'] == 'Buy' and int(row['Amount']) >= 0:
                stockList.append(ticker)
                newStock = {'Ticker':ticker,'Amount':int(row['Amount']),'BuyInPrice':round(float(row['Price']), 2),'CurrentPrice':"",'Gain':""}
                portfolioGain.append(newStock)
                # If no valid ticker were found
                # else:
                #     response = webapp.response_class(
                #     response=json.dumps("Credential file contains invalid ticker. Please check again."),
                #     status=400,
                #     mimetype='application/json'
                #     )
                #     print(response)
                #     return response

        # Call stockAPI to get the current price of each ticker
        currentPriceList, validBool = Config.stockAPI.liveQuotes(stockList)
        print(currentPriceList, validBool)

        # Check if stockAPI.liveQuotes works
        if validBool:
            i = 0
            for stock in portfolioGain:
                stock['CurrentPrice'] = round(float(currentPriceList[i]),2)
                i += 1
                stock['Gain'] = round(100 * (stock['CurrentPrice'] - stock['BuyInPrice']) / stock['BuyInPrice'], 2)
            print(portfolioGain)
        else:
            # response = webapp.response_class(
            # response=json.dumps("Access to stockAPI.liveQuotes failed."),
            # status=400,
            # mimetype='application/json'
            # )
            response = {
                "statusCode": 400,
                "headers": {'Content-Type': 'application/json'},
                "body": 'Ticker should not be empty.'
            }
            print(response)
            return response
            
    # When user uploads an empty credential or chooses to start from scratch   
    else:
        portfolioGain = [{'Ticker':'', 'Amount':'', 'BuyInPrice':'', 'CurrentPrice':'', 'Gain':''}]

    return wrap(render_template_without_flask(
        "portfolioEditor.html", 
        portfolioGain = portfolioGain, 
        dictCredential = dictCredential, 
        clientIP = clientIP))


# @webapp.route('/stock', methods=['POST'])
def browseStock(event, context):
    """
    Stock Page
    Same as @webapp.route('/stock/<ticker>'), but different method
    """
    # ticker = request.form.get('key')
    print(event['body'])
    body_raw = str(event['body'])
    tmp = body_raw.split('form-data; name=\"key\"\r\n\r\n')[1]
    ticker = tmp.split('\r\n-')[0]
    length = 390
    df, valid = Config.stockAPI.dailyQuote(ticker)

    if valid:
        closeData = df.loc[:, "close"]
        timeData = df.index
        volumeData = df.loc[:, "volume"]

        pricedata = closeData.to_list()
        xlabels = timeData.to_list()
        actiondata = volumeData.to_list()

        return wrap(render_template_without_flask("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               ))
    else:  # ticker DNE
        # # ==================== Test data ========================
        # length = 60
        # pricedata = np.random.random(length)
        # pricedata = (pricedata * 10).tolist()
        # actiondata = np.random.random(length).tolist()
        # xlabels = np.arange(length).tolist()
        # # ==================== End Test ====================
        return wrap(render_template_without_flask("invalidTicker.html"))
        # return wrap(render_template_without_flask("stock.html",
        #                        xlabels=xlabels,
        #                        price=pricedata,
        #                        action=actiondata,
        #                        name=ticker
        #                        ))



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
