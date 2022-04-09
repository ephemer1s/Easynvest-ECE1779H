from datetime import datetime
# from flask import Flask, request, jsonify, session
# from flask_cors import CORS, cross_origin
import json
from json import JSONEncoder
import os
from markupsafe import escape
from twelvedata import TDClient
from twelvedata.exceptions import BadRequestError
import pandas
import http.client
import requests
import datetime

try:
    from credential import Config_StockAPI
except:
    from tools.credential import Config_StockAPI


class StockData(object):
    def __init__(self):
        self.API_KEY = Config_StockAPI.API_KEY
        self.header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                       'Accept-Encoding': 'none',
                       'Accept-Language': 'en-US,en;q=0.8',
                       'Connection': 'keep-alive'}
        self.td = TDClient(apikey=self.API_KEY)

    def dailyQuote(self, ticker):
        """
        Args:
            ticker (string): Ticker of stock

        Returns:
            df: Panda Dataframe of daily quote
        """

        validBool = False

        # ts = self.td.time_series(
        #     symbol=ticker,
        #     interval="1min",
        #     outputsize=1000,
        #     timezone="Exchange",
        #     date="today",
        #     order='ASC'
        # )

        # Returns pandas.DataFrame

        lastWeekday = datetime.datetime.today() - datetime.timedelta(days=(0, 0, 0, 0,
                                                                           0, 1, 2)[datetime.datetime.today().weekday()])
        lastWeekdayStr = lastWeekday.strftime('%m-%d-%y')

        ts = self.td.time_series(
            symbol=ticker,
            interval="1min",
            outputsize=1000,
            timezone="Exchange",
            date=lastWeekdayStr,
            order='ASC'
        )
        # Returns pandas.DataFrame
        try:
            df = ts.as_pandas()
            validBool = True
        except:
            df = ""
            validBool = False

        return df, validBool

    def getLogo(self, ticker):
        """Get logo of the ticker; Ideally should store in S3 to avoid calling too many times

        Args:
            ticker (string): Ticker of stock

        Returns:
            response(Bytes?): The image itself
            string: url of the logo
        """
        validBool = False
        logo = self.td.get_logo(symbol=ticker,)

        try:
            url = logo.as_json()["url"]

            r = requests.get(url, allow_redirects=True, headers=self.header)
            validBool = True
        except:
            url = ""
            r = ""
            validBool = False
        return r, url, validBool

    def liveQuotes(self, tickers):
        """live Quotes of the stock

        Args:
            tickers (list): Tickers of stocks

        Returns:
            float: The price opf the stock
        """

        validBool = False
        ts = self.td.price(
            symbol=tickers,
        )

        # Returns pandas.DataFrame
        liveQuotes = []
        try:
            liveQuote = ts.as_json()

            for i in liveQuote:
                liveQuotes.append(liveQuote[i]["price"])
            validBool = True
        except:
            liveQuotes = []
            validBool = False

        return liveQuotes, validBool


# TESTING -----------------------------
if __name__ == '__main__':

    stockAPI = StockData()

    r, url, _ = stockAPI.getLogo("V")
    df, _ = stockAPI.dailyQuote("V")
    # liveQuote, _ = stockAPI.liveQuote("V")
    liveQuotes, _ = stockAPI.liveQuotes(["V", "MGA", "AAPL"])
    print(_)
    print(liveQuotes)
    print(df.to_string(), url)
    pass
    # --------------------------------------
