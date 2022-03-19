from datetime import datetime, timedelta

import boto3
from tools.credential import ConfigAWS


def newCloudwatch(aws_access_key_id, aws_secret_access_key):
    '''
    '''
    return boto3.client('cloudwatch', 
                        region_name='us-east-1',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key)


# Put custom metrics
def putCacheMissRate(missrate, instance_name):
    '''
    Send Memcache Miss Rate to AWS Cloudwatch. Return a response message.
    missrate: value to send
    instance_name: current memcache instance identifier (could be anything based on your implementation)
    '''
    print('Sending Cache Miss Rate to Cloudwatch')
    cloudwatch = newCloudwatch(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
    response = cloudwatch.put_metric_data(
        MetricData = [{
                'MetricName': 'miss_rate',
                'Dimensions': [{
                        'Name': 'instance',
                        'Value': instance_name
                    }],
                'Unit': 'Percent',
                'Value': missrate}],
        Namespace = 'ece1779/memcache')
    print(response)
    return response


# Get list metrics through the pagination interface
def getCacheMissRateData(instances: list):
    '''
    Get miss rate from a specified server from cloudwatch. return a dict containing responses.
    '''
    cloudwatch = newCloudwatch(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
    responses = []
    for i in instances:
        responses.append(
            # TODO: Add responses
        )
    return responses


def getCacheMissRateStatistics(instances: list):
    '''
    '''
    cloudwatch = newCloudwatch(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
    responses = []
    for i in instances:
        responses.append(
            cloudwatch.get_metric_statistics(
                Namespace='ece1779/memcache',
                MetricName='miss_rate',
                Dimensions=[{
                        "Name": "instance",
                        "Value": i
                    }],
                StartTime = datetime.utcnow() - timedelta(seconds = 3600),
                EndTime = datetime.utcnow(),
                Period=60,
                Statistics=['Average'],
                Unit='Percent',
            )
        )
    return responses


if __name__ == '__main__':
    print('Testing Cloudwatch APIs...........')

    print('Finished')
