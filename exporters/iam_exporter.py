import boto3
import time
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID  # Importando o ID da conta

iam_client = boto3.client('iam')

# Prometheus Gauges
iam_users_gauge = Gauge('aws_iam_users_total', 'Total number of IAM users', ['account_id'])
iam_access_keys_gauge = Gauge('aws_iam_access_keys_old', 'Number of IAM access keys older than X days', ['account_id'])

# Set the threshold for IAM access keys age
ACCESS_KEY_AGE_THRESHOLD = 90

def collect_iam_metrics():
    users = iam_client.list_users()['Users']
    iam_users_gauge.labels(account_id=ACCOUNT_ID).set(len(users))

    old_keys_count = 0
    for user in users:
        access_keys = iam_client.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
        for key in access_keys:
            age = (time.time() - key['CreateDate'].timestamp()) / (60 * 60 * 24)
            if age > ACCESS_KEY_AGE_THRESHOLD:
                old_keys_count += 1

    iam_access_keys_gauge.labels(account_id=ACCOUNT_ID).set(old_keys_count)
