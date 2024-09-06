import boto3
import time
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID  # Importing the account ID
from botocore.exceptions import ClientError

iam_client = boto3.client('iam')

# Prometheus Gauges
iam_users_gauge = Gauge('aws_iam_users_total', 'Total number of IAM users', ['account_id'])
iam_access_keys_gauge = Gauge('aws_iam_access_keys_old', 'Number of IAM access keys older than X days', ['account_id'])
iam_unused_keys_gauge = Gauge('aws_iam_access_keys_unused', 'Number of IAM access keys not used in the last 30 days', ['account_id'])  # Renamed metric

# Set the threshold for IAM access keys age and usage
ACCESS_KEY_AGE_THRESHOLD = 90
ACCESS_KEY_UNUSED_THRESHOLD = 30

def collect_iam_metrics():
    try:
        old_keys_count = 0
        unused_keys_count = 0
        users = []
        
        # Paginate through all IAM users
        paginator = iam_client.get_paginator('list_users')
        for page in paginator.paginate():
            users.extend(page['Users'])
        
        # Set the total number of IAM users in Prometheus gauge
        iam_users_gauge.labels(account_id=ACCOUNT_ID).set(len(users))
        
        # Loop through users and get their access keys
        for user in users:
            access_key_paginator = iam_client.get_paginator('list_access_keys')
            for key_page in access_key_paginator.paginate(UserName=user['UserName']):
                for key in key_page['AccessKeyMetadata']:
                    age = (time.time() - key['CreateDate'].timestamp()) / (60 * 60 * 24)
                    if age > ACCESS_KEY_AGE_THRESHOLD:
                        old_keys_count += 1
                    
                    # Get the last used date for each key
                    last_used_response = iam_client.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                    last_used_date = last_used_response.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                    
                    # Check if the key has been used in the last 30 days
                    if last_used_date:
                        days_since_last_used = (time.time() - last_used_date.timestamp()) / (60 * 60 * 24)
                        if days_since_last_used > ACCESS_KEY_UNUSED_THRESHOLD:
                            unused_keys_count += 1
                    else:
                        # If there is no record of the key being used, it counts as unused
                        unused_keys_count += 1

        # Set the number of old access keys and unused access keys in Prometheus gauges
        iam_access_keys_gauge.labels(account_id=ACCOUNT_ID).set(old_keys_count)
        iam_unused_keys_gauge.labels(account_id=ACCOUNT_ID).set(unused_keys_count)

    except ClientError as e:
        print(f"Error fetching IAM metrics: {e}")
