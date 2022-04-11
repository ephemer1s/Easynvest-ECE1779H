# lambda-apigw.py --
# used for render templates without flask application
# author: ephemer1s

import json
import os
from datetime import datetime, timedelta
import jinja2
import numpy as np
# from flask import *  # ephemer1s: if there is no web app, you should not import flask.
import requests
from frontEnd.config import Config


def render_template_without_flask(template_name, **template_vars):
    """
    Usage is the same as flask.render_template:
    render_template('my_template.html', var1='foo', var2='bar')
    """
    if os.path.exists('./frontEnd/templates'):
        template_path = './frontEnd/templates'
    else:
        template_path = './templates'

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


# # @webapp.route('/')
# def index():
#     """
#     Main Page
#     Returns: 'Main Page' rendered by flask
#     """
#     # Under Construction
#     # Need to fill price & value before deployment
#     nasdaqCurrentPrice = 182
#     nasdaqCurrentInterest = -0.18
#     return wrap(render_template_without_flask("mainpage.html", nasdaqCurrentPrice=nasdaqCurrentPrice, nasdaqCurrentInterest=nasdaqCurrentInterest))


# @webapp.route('/home')
def home(event, context):
    """Home Page: Call to go back to main page "/"

    Returns:
        html of Main Page
    """
    return wrap(render_template_without_flask("mainpage.html"))


# @webapp.route('/portfolio')
def portfolio(event, context):
    """
    Portfolio Page
    Returns: 'Portfolio Page' html
    """
    return wrap(render_template_without_flask("portfolioLogin.html"))


# @webapp.route('/stockRedirect', methods=['GET', 'POST'])
def stockRedirect(event, context):
    """
    Get input client stock ticker fron ticker search bar and redirect to /stock/<ticker>
    """
    # TODO @ephemer1s handler debug, should this be working?
    # stockTicker = request.form.get('stockTicker', "")
    stockTicker = event['stockTicker']

    if not stockTicker:  # If ticker is empty, raise error
        # TODO @ephemer1s handler debug, should this be working?
        # response = webapp.response_class(
        #     response=json.dumps("Ticker should not be empty."),
        #     status=400,
        #     mimetype='application/json'
        # )
        
        response = {
            "statusCode": 400,
            "headers": {'Content-Type': 'application/json'},
            "body": 'Ticker should not be empty.'
        }
        print(response)
        return response

    # Under Construction @ Haozhe
    # Add ticker not found later
    # TODO @ephemer1s handler debug, should this be working?
    # return redirect("/stock/" + str(stockTicker))
    return stock(stockTicker)


# @webapp.route('/portfolioParse')
def portfolioParse(event, context):
    """
    Get uploaded csv credential from client and parse it for edit
    """

    # Under Construction @ Haozhe
    # Parse csv file, pass info and redirect to portfolioEditor.html
    return wrap(render_template_without_flask("portfolioEditor.html"))


# @webapp.route('/portfolioEditor')
def portfolioEditor(event, context):
    """
    Get uploaded csv credential from client and display for edit
    Returns: 'Portfolio Editor Page' html
    """

    # Under Construction
    return wrap(render_template_without_flask("portfolioEditor.html"))


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

        return wrap(render_template_without_flask("stock.html",
                               xlabels=lastDayNewXlabels,
                               price=lastDayPricedata,
                               action=lastDayActiondata,
                               name=chartName
                               ))
    else:  # ticker DNE
        # ==================== Test data ========================
        length = 60
        pricedata = np.random.random(length)
        pricedata = (pricedata * 10).tolist()
        actiondata = np.random.random(length).tolist()
        xlabels = np.arange(length).tolist()
        # ==================== End Test ====================
        print("using test data")
        return wrap(render_template_without_flask("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               ))


# @webapp.route('/stock', methods=['POST'])
def browseStock(event, context):
    """
    Stock Page
    Same as @webapp.route('/stock/<ticker>'), but different method
    """
    # TODO @ephemer1s handler debug, should this be working?
    # ticker = request.form.get('key')
    ticker = event['key']
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
        # ==================== Test data ========================
        length = 60
        pricedata = np.random.random(length)
        pricedata = (pricedata * 10).tolist()
        actiondata = np.random.random(length).tolist()
        xlabels = np.arange(length).tolist()
        # ==================== End Test ====================
        return wrap(render_template_without_flask("stock.html",
                               xlabels=xlabels,
                               price=pricedata,
                               action=actiondata,
                               name=ticker
                               ))


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
