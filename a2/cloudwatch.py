import boto3


# Put custom metrics
def putCacheMissRate(missrate, instance_name):
    '''
    Send Memcache Miss Rate to AWS Cloudwatch. Return a response message.
    missrate: value to send
    instance_name: current memcache instance identifier (could be anything based on your implementation)
    '''
    print('Sending Cache Miss Rate to Cloudwatch')
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    response = cloudwatch.put_metric_data(
        MetricData = [{
                'MetricName': 'miss_rate',
                'Dimensions': [{
                        'Name': 'instance',
                        'Value': instance_name
                    }],
                'Unit': 'percentage',
                'Value': missrate}],
        Namespace = 'ece1779/memcache')
    print(response)
    return response


# Get list metrics through the pagination interface
def getCacheMissRate(instances: list):
    '''
    Get miss rate from a specified server from cloudwatch. return a dict containing responses.
    '''
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    paginator = cloudwatch.get_paginator('list_metrics')
    responses = {}
    for i in instances:
        response = paginator.paginate(
            Dimensions=[{
                'Name': 'instance',
                'Value': i}],
            MetricName='miss_rate',
            Namespace='ece1779/memcache')
        for content in response:
            print(content['Metrics'])
        responses[i] = response
    return responses


if __name__ == '__main__':
    print('Testing Cloudwatch APIs...........')
    putCacheMissRate(1.14, str(5.14))
    print('Finished')
