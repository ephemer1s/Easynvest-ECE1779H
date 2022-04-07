import base64

try:
    from backEnd.config import backEndConfig
except:
    from config import backEndConfig


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
