import boto3

def get_account_id():
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    return account_id

ACCOUNT_ID = get_account_id()