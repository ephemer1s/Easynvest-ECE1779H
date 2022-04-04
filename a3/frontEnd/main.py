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
    Returns: index.html 'Main Page' rendered by flask
    """
    return render_template("index.html")


@webapp.route('/stock/<ticker>')
def stock(ticker):
    """
    Stock Page
    Input:
     - ticker: str, 3-5 letter company name abbreviation
    Returns: stock.html of specific company rendered by flask
    """
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


@webapp.route('/stock', methods=['POST'])
def browseStock():
    """
    Stock Page
    Same as @webapp.route('/stock/<ticker>'), but different method
    """
    ticker = request.form.get('key')
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

