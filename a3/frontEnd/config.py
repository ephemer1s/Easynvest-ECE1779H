from tools.stockAPI import StockData


class Config():
    chart_len = 390                  # how many data is displayed in chart
    chart_size = (0, 0)             # size of the chart by pixel
    stockAPI = StockData()
