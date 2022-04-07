try:
    from tools.credential import ConfigAWS
    from tools.awsS3 import S3_Class
    from tools.stockAPI import StockData
except:

    import sys
    import os

    # getting the name of the directory
    # where the this file is present.
    current = os.path.dirname(os.path.realpath(__file__))

    # Getting the parent directory name
    # where the current directory is present.
    parent = os.path.dirname(current)

    # adding the parent directory to
    # the sys.path.
    sys.path.append(parent)
    from tools.credential import ConfigAWS
    from tools.awsS3 import S3_Class
    from tools.stockAPI import StockData

import boto3


class backEndConfig(object):
    s3_client = boto3.client('s3',
                             "us-east-1",
                             aws_access_key_id=ConfigAWS.aws_access_key_id,
                             aws_secret_access_key=ConfigAWS.aws_secret_access_key)

    s3 = S3_Class(s3_client)
    s3.initialize_bucket()
    stockAPIObject = StockData()
