import boto3
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID

# Prometheus Gauges
ec2_instances_gauge = Gauge('aws_ec2_instances_total', 'Total number of EC2 instances', ['account_id', 'region'])
ec2_instance_types_gauge = Gauge('aws_ec2_instance_types', 'Number of EC2 instances by type', ['account_id', 'region', 'instance_type'])

def collect_ec2_metrics(region='us-east-1'):
    ec2_client = boto3.client('ec2', region_name=region)

    instances = ec2_client.describe_instances()['Reservations']
    total_instances = sum(len(reservation['Instances']) for reservation in instances)
    ec2_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_instances)

    instance_type_count = {}
    for reservation in instances:
        for instance in reservation['Instances']:
            instance_type = instance['InstanceType']
            if instance_type not in instance_type_count:
                instance_type_count[instance_type] = 0
            instance_type_count[instance_type] += 1

    for instance_type, count in instance_type_count.items():
        ec2_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type).set(count)
