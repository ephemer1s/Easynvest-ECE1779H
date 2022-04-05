from datetime import datetime
# from flask import Flask, request, jsonify, session
# from flask_cors import CORS, cross_origin
import json
from json import JSONEncoder
import os
from markupsafe import escape
from twelvedata import TDClient
import pandas
import http.client
import requests

# AlphaVantage API_key = RSZQ3NC9FB0HLZ1U
# Rapid_API key = ea92b8480emshfbaf69ffd47e81ep1e77d1jsn4d6bc9940fd7

# 12 API Key: 7a0f20e13dd14cc89645d8c47c02e181


class Config_StockAPI():

    API_KEY = "7a0f20e13dd14cc89645d8c47c02e181"  # Change this to our own API KEY!


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
        ts = self.td.time_series(
            symbol=ticker,
            interval="1min",
            outputsize=1000,
            timezone="Exchange",
            date="today"
        )

        # Returns pandas.DataFrame
        df = ts.as_pandas()

        return df

    def getLogo(self, ticker):
        """Get logo of the ticker; Ideally should store in S3 to avoid calling too many times

        Args:
            ticker (string): Ticker of stock

        Returns:
            response(Bytes?): The image itself
            string: url of the logo
        """
        logo = self.td.get_logo(symbol=ticker,)

        url = logo.as_json()["url"]

        r = requests.get(url, allow_redirects=True, headers=self.header)

        return r, url

    def liveQuote(self, ticker):
        """live Quote of the stock

        Args:
            ticker (string): Ticker of stock

        Returns:
            float: The price opf the stock
        """
        ts = self.td.price(
            symbol=ticker,
        )

        # Returns pandas.DataFrame
        liveQuote = ts.as_json()["price"]

        return liveQuote


# TESTING -----------------------------
if __name__ == '__main__':
    # print(stock("daily", "AAPL"))
    stockAPI = StockData()

    r, url = stockAPI.getLogo("V")
    df = stockAPI.dailyQuote("V")
    liveQuote = stockAPI.liveQuote("V")
    print(liveQuote)
    print(df.to_string(), url)
    pass
# --------------------------------------
