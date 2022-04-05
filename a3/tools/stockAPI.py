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

{
    # def stock(intent, ticker):
    #     intent = escape(intent)
    #     stockTicker = escape(ticker)

    #     if intent == "daily":
    #         # query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=
    #         if stockTicker != "":
    #             conn = http.client.HTTPSConnection("www.alphavantage.co")
    #             API_key = "RSZQ3NC9FB0HLZ1U"
    #             conn.request(
    #                 "GET", f"/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=1min&outputsize=full&apikey={API_key}")
    #             res = conn.getresponse()
    #             data = res.read()
    #             stockData = (data.decode("utf-8"))
    #             json_acceptable_string = stockData.replace("'", "\"")
    #             stockDataDict = json.loads(json_acceptable_string)
    #             if (not "Error Message" in stockDataDict):

    #                 # Process data to digestable 9:30 to 4:00 time series

    #                 dailyCloseList = []
    #                 dailyTimeList = []

    #                 for timeKeys in stockDataDict["Time Series (1min)"]:
    #                     timestamp = datetime.strptime(
    #                         timeKeys, '%Y-%m-%d %H:%M:%S')
    #                     openTime = datetime.strptime(
    #                         timeKeys[:-8] + "09:29:59", '%Y-%m-%d %H:%M:%S')
    #                     closeTime = datetime.strptime(
    #                         timeKeys[:-8] + "16:00:01", '%Y-%m-%d %H:%M:%S')
    #                     if timestamp >= openTime and timestamp <= closeTime:
    #                         dailyCloseList.append(
    #                             stockDataDict["Time Series (1min)"][timeKeys]["4. close"])
    #                         dailyTimeList.append(timeKeys)

    #                 returnDict = dict(zip(dailyTimeList, dailyCloseList))

    #                 return json.dumps({"statusCode": 200,
    #                                    "stockInfo": returnDict
    #                                    })
    #             else:
    #                 message = "Symbol \"" + stockTicker + "\" Not Found. "
    #                 return json.dumps({"statusCode": 400,
    #                                    "message": message
    #                                    })
    #         else:
    #             return json.dumps({"statusCode": 400, "Usage": "Enter stock Ticker to receive daily time series."})

    #     elif intent == "quote":

    #         # example
    #         if stockTicker != "":
    #             # connect to stock api and get quote

    #             # Temporary Stock API

    #             conn = http.client.HTTPSConnection("www.alphavantage.co")

    #             API_key = "RSZQ3NC9FB0HLZ1U"
    #             conn.request(
    #                 "GET", f"/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_key}")

    #             res = conn.getresponse()
    #             data = res.read()
    #             stockData = (data.decode("utf-8"))
    #             json_acceptable_string = stockData.replace("'", "\"")
    #             stockDataDict = json.loads(json_acceptable_string)

    #             if (stockDataDict["Global Quote"]):

    #                 return json.dumps({"statusCode": 200,
    #                                    "stockInfo": stockDataDict,
    #                                    })

    #             else:
    #                 message = "Symbol \"" + stockTicker + "\" Not Found. "
    #                 return json.dumps({"statusCode": 400,
    #                                    "message": message
    #                                    })
    #         else:
    #             return json.dumps({"statusCode": 400, "Usage": "Enter stock Ticker to receive quote."})
}


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
        logo = self.td.get_logo(symbol=ticker,)

        url = logo.as_json()["url"]

        r = requests.get(url, allow_redirects=True, headers=self.header)

        return r, url

    def liveQuote(self, ticker):
        ts = self.td.price(
            symbol=ticker,
        )

        # Returns pandas.DataFrame
        df = ts.as_json()["price"]

        return df


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
