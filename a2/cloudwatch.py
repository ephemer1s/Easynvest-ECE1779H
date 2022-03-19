import time
from datetime import datetime, timedelta

import boto3
from tools.credential import ConfigAWS


def createCloudwatchClient(aws_access_key_id, aws_secret_access_key):
    '''
    Generate a cloudwatch client.
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
    cloudwatch = createCloudwatchClient(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
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
    Get miss rate DATA from a specified server from cloudwatch. return a dict containing responses.
    This function is bad, and I no longer maintenance it.
    use this one below instead. -> getCacheMissRateStatistics(instances: list, interval=60, period=60)
    '''
    cloudwatch = createCloudwatchClient(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
    responses = []
    for i in instances:
        responses.append(
            # TODO: Add responses
            cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {}
                ],
                StartTime = datetime.utcnow() - timedelta(seconds = interval),
                EndTime = datetime.utcnow(),
                NextToken='string',
                ScanBy='TimestampDescending'|'TimestampAscending',
                MaxDatapoints=123
            )
        )
    return responses


def getCacheMissRateStatistics(instances: list, interval=60, period=60):
    '''
    Get miss rate STATISTICS from a specified server from cloudwatch. return a dict containing responses.
    retrieve the average missrate value in responses[i]['Datapoints'][-1]['Average']
    instances: List of instance names used to specify the dimension of metrics
    interval:  Starttime = Endtime - interval
    period:    of which to be calculated together as average. 
               len(responses[i]['Datapoints']) == interval // periods
    '''
    cloudwatch = createCloudwatchClient(ConfigAWS.aws_access_key_id, ConfigAWS.aws_secret_access_key)
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
                StartTime = datetime.utcnow() - timedelta(seconds = interval),
                EndTime = datetime.utcnow(),
                Period=period,
                Statistics=['Average'],
                Unit='Percent',
            )
        )
    return responses


if __name__ == '__main__':
    print('Testing Cloudwatch APIs...........')
    for i in range(60):
        print(str(i) + '.................')
        putCacheMissRate(i * 0.01, 'test2')
        time.sleep(10)
    response = getCacheMissRateStatistics(['test2'], interval=600, period=60)
    print(response)

    with open("./logs/cloudwatch.log", 'a') as f:
        f.write(str(response))
    print('Finished')
