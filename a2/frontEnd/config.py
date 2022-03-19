from tools.credential import ConfigAWS
import boto3
from tools.awsS3 import S3_Class


class Config():

    db_config = {'user': 'root',
                 'password': '19410524',
                 'host': 'database-1.clriqywhb6pw.us-east-1.rds.amazonaws.com',
                 'database': 'database-a1'}
    UPLOAD_FOLDER = './uploads/'
    memcacheIP_List = []
    s3_client = boto3.client('s3',
                             "us-east-1",
                             aws_access_key_id=ConfigAWS.aws_access_key_id,
                             aws_secret_access_key=ConfigAWS.aws_secret_access_key)

    s3 = S3_Class(s3_client)
