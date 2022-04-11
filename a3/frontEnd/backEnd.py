import base64
import boto3
import sys
import os

try:
    from tools.credential import ConfigAWS
    from tools.awsS3 import S3_Class
    from tools.stockAPI import StockData
except:
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


class backEndConfig(object):
    s3_client = boto3.client('s3',
                             "us-east-1",
                             aws_access_key_id=ConfigAWS.aws_access_key_id,
                             aws_secret_access_key=ConfigAWS.aws_secret_access_key)

    s3 = S3_Class(s3_client)
    s3.initialize_bucket()
    stockAPIObject = StockData()



def loadLogo(ticker: str):
    """Load the logo for given ticker. Use S3 and API.
    Will first check if S3 has it.
    """

    # First look for S3
    ExistOnS3 = backEndConfig.s3.check_if_file_exist(ticker+".png")
    validBoolReturn = False

    base64FormatImage = None
    if ExistOnS3:
        base64FormatImage = backEndConfig.s3.get_file_in_base64(ticker+".png")
        validBoolReturn = True
    else:
        # pull from api and store on s3
        r, url, validBool = backEndConfig.stockAPIObject.getLogo(ticker)

        if validBool:

            base64FormatImage = base64.b64encode(r.content).decode()
            validBoolReturn = True
            backEndConfig.s3.upload_public_inner_file(r.content, ticker+".png")

        else:
            # Ticker DNE
            pass

    return base64FormatImage, validBoolReturn


if __name__ == '__main__':
    base64Image, valid = loadLogo("AAPL")
