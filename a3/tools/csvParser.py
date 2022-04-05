
# importing csv module
import csv
import pandas as pd

# initializing the titles and rows list
fields = []
rows = []


def readCSV(filename):
    
    df = pd.read_csv(filename)
    return df

