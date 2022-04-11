from tools.stockAPI import StockData
import boto3
from tools.awsS3 import S3_Class
from tools.credential import ConfigAWS


class Config():
    chart_len = 390                 # how many data is displayed in chart
    chart_size = (0, 0)             # size of the chart by pixel
    stockAPI = StockData()

    s3_client = boto3.client('s3',
                             "us-east-1",
                             aws_access_key_id=ConfigAWS.aws_access_key_id,
                             aws_secret_access_key=ConfigAWS.aws_secret_access_key)

    s3 = S3_Class(s3_client)