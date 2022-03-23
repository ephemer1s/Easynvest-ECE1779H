import boto3
import botocore
from botocore.exceptions import ClientError
import os
try:
    from tools.credential import ConfigAWS
except:
    from credential import ConfigAWS
import base64

# Create a credential.py in tools/ with the code as following format:

# class ConfigAWS():
#     aws_access_key_id = "You wish"
#     aws_secret_access_key = "Fuck you"

# Credits: https://www.youtube.com/watch?v=qsPZL-0OIJg


class S3_Class(object):
    def __init__(self, s3_client):
        self.s3_client = s3_client
        self.bucketName = "ece1779-assignment-2"

    def initialize_bucket(self):
        response = self.s3_client.list_buckets()['Buckets']

        name = self.bucketName
        bucketExist = False
        # print(response)
        for dict in response:
            if dict['Name'] == name:
                bucketExist = True

        if not bucketExist:
            self.s3_client.create_bucket(Bucket=name)

    def upload_file(self, _file_name, _object_name=None, _args=None):
        '''
            _file_name: name of file on local
            _bucket: bucket name
            _object_name: name of file on S3
            _args: custom args
        '''
        if _object_name is None:
            _object_name = _file_name

        if not os.path.isfile(_file_name):
            print("local file DNE. (Should not happen)")
            return False

        response = self.s3_client.upload_file(
            _file_name, self.bucketName, _object_name, ExtraArgs=_args)
        print("Uploaded "+_file_name + " to S3.")
        return True

    def upload_public_file(self, _file_name, _bucket, _object_name=None):

        return self.upload_file(_file_name, _bucket, _object_name=_object_name, _args={'ACL': 'public-read'})

    def upload_inner_file(self, _file, _object_name):
        '''
            _file: data in binary
            _object_name: name of file on S3
            _args: custom args
        '''
        self.s3_client.put_object(
            Body=_file, Bucket=self.bucketName, Key=_object_name)

        print("Uploaded "+_object_name + " to S3.")
        return True

    def upload_public_inner_file(self, _file, _object_name):
        '''
            _file: data in binary
            _object_name: name of file on S3
            _args: custom args
        '''
        self.s3_client.put_object(
            Body=_file, Bucket=self.bucketName, Key=_object_name, ACL='public-read')

        print("Uploaded "+_object_name + " to S3.")
        return True

    def download_file(self, _filename, _download_folder):
        """ Download image to the _download_folder

        Args:
            _filename (string): filename
            _download_folder (string): folder in a2/
        """
        if 'Contents' in self.s3_client.list_objects(Bucket=self.bucketName):
            bucketList = self.s3_client.list_objects(
                Bucket=self.bucketName)['Contents']

            fileList = []
            for file in bucketList:
                fileList.append(file['Key'])
                # print(file['Key'])

            filename = os.path.join(_download_folder, _filename)
            # print("filename : ", filename)
            filename = filename.replace('\\', '/')

            # check if _filename exist on S3:
            if _filename in fileList:
                if not os.path.isdir(_download_folder):
                    os.mkdir(_download_folder)
                self.s3_client.download_file(
                    self.bucketName, _filename, filename)
                print("File Downloaded to "+filename)
                return True
            else:
                print("File DNE on S3.")
                return False
        else:
            print("File DNE on S3.")
            return False

    def delete_file(self, _filename):
        if 'Contents' in self.s3_client.list_objects(Bucket=self.bucketName):
            bucketList = self.s3_client.list_objects(
                Bucket=self.bucketName)['Contents']

            fileList = []
            for file in bucketList:
                fileList.append(file['Key'])
                # print(file['Key'])

            # check if _filename exist on S3:
            if _filename in fileList:
                self.s3_client.delete_object(
                    Bucket=self.bucketName, Key=_filename)
                print(_filename+" deleted.")
                return True
            else:
                print("File DNE on S3.")
                return False
        else:
            print("File DNE on S3.")
            return False

    def delete_all(self):
        if 'Contents' in self.s3_client.list_objects(Bucket=self.bucketName):
            for obj in self.s3_client.list_objects(Bucket=self.bucketName)['Contents']:
                self.s3_client.delete_object(
                    Bucket=self.bucketName, Key=obj['Key'])
            return True
        else:
            return True

    def get_file(self, _filename):
        if 'Contents' in self.s3_client.list_objects(Bucket=self.bucketName):
            bucketList = self.s3_client.list_objects(
                Bucket=self.bucketName)['Contents']

            fileList = []
            for file in bucketList:
                fileList.append(file['Key'])
                # print(file['Key'])

            # check if _filename exist on S3:
            if _filename in fileList:
                object = self.s3_client.get_object(
                    Bucket=self.bucketName, Key=_filename)
                print(_filename+" gotten.")
                return object['Body'].read()
            else:
                print("File DNE on S3.")
                return False
        else:
            print("File DNE on S3.")
            return False

    def check_if_file_exist(self, _filename):
        if 'Contents' in self.s3_client.list_objects(Bucket=self.bucketName):
            bucketList = self.s3_client.list_objects(
                Bucket=self.bucketName)['Contents']

            fileList = []
            for file in bucketList:
                fileList.append(file['Key'])
                # print(file['Key'])

            # check if _filename exist on S3:
            if _filename in fileList:
                return True
            else:
                print("File DNE on S3.")
                return False
        else:
            print("File DNE on S3.")
            return False

    def get_file_in_base64(self, _filename):
        return base64.b64encode(self.get_file(_filename)).decode()


# # Calling Area ######################################################################
# try:
#     s3_client = boto3.client('s3',
#                              "us-east-1",
#                              aws_access_key_id=ConfigAWS.aws_access_key_id,
#                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
#     call_obj = S3_Class(s3_client)

#     call_obj.initialize_bucket()
#     # print(os.getcwd())
#     print(call_obj.upload_public_file(
#         "tools/imageFolder/a.jpeg", call_obj.bucketName, _object_name="a.jpeg"))

#     call_obj.download_file("a.jpeg", './uploads/')

#     content = call_obj.get_file_in_base64("a.jpeg")

#     print(content)
#     call_obj.delete_file("a.jpeg")

# except ClientError as e:
#     print("There is an error in the client configuration: ", e)

# # Calling Area ######################################################################
