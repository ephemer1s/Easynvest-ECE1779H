import boto3
from tools.credential import ConfigAWS

class CloudwatchAPI(object):

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        self.client = boto3.client('cloudwatch', 
                                    region_name='us-east-1',
                                    aws_access_key_id=aws_access_key_id,
                                    aws_secret_access_key=aws_secret_access_key)


    def putEvent(self, event, name):
        '''
        Send Memcache Miss Rate to AWS Cloudwatch. Return a response message.
        missrate: value to send
        instance_name: current memcache instance identifier (could be anything based on your implementation)
        '''
        response = self.client.put_metric_data(
            MetricData = [{
                    'MetricName': 'miss_rate',
                    'Dimensions': [{
                            'Name': 's3',
                            'Value': name
                        }],
                    'Unit': 'None',
                    'Value': event}],
            Namespace = 'ece1779/a3')
        return response


def s3_watch(event, context):
    client = CloudwatchAPI(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
    # Upon success
    if event is not None:
        print(event)
        client.putEvent(1, 'create')
    pass
    
    # TODO implement