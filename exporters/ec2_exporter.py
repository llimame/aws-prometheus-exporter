from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Prometheus Gauges for EC2 Instances
ec2_instances_gauge = Gauge('aws_ec2_instances_total', 'Total number of EC2 instances', ['account_id', 'region'])
ec2_instance_types_gauge = Gauge('aws_ec2_instance_types', 'Number of EC2 instances by type and lifecycle', ['account_id', 'region', 'instance_type', 'lifecycle'])

# New Gauge for Reserved Instances
reserved_instances_gauge = Gauge('aws_ec2_reserved_instances_total', 'Total number of Reserved EC2 Instances', ['account_id', 'region'])
reserved_instance_types_gauge = Gauge('aws_ec2_reserved_instance_types', 'Number of Reserved EC2 Instances by type', ['account_id', 'region', 'instance_type', 'lifecycle'])

def collect_ec2_metrics(region='us-east-1'):
    ec2_client = boto3.client('ec2', region_name=region)

    try:
        paginator = ec2_client.get_paginator('describe_instances')
        total_instances = 0
        instance_type_count = {}

        # Handle paginated responses for EC2 instances
        for page in paginator.paginate():
            instances = page['Reservations']
            total_instances += sum(len(reservation['Instances']) for reservation in instances)

            for reservation in instances:
                for instance in reservation['Instances']:
                    instance_type = instance['InstanceType']
                    lifecycle = instance.get('InstanceLifecycle', 'normal')  # 'spot' if spot instance, else 'normal'

                    # Initialize the dictionary if it doesn't exist
                    if instance_type not in instance_type_count:
                        instance_type_count[instance_type] = {'spot': 0, 'normal': 0}
                    
                    # Count based on lifecycle
                    instance_type_count[instance_type][lifecycle] += 1

        # Update Prometheus Gauges for EC2 instances
        ec2_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_instances)
        for instance_type, counts in instance_type_count.items():
            for lifecycle, count in counts.items():
                ec2_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type, lifecycle=lifecycle).set(count)

    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching EC2 metrics: {e}")


def collect_reserved_instance_metrics(region='us-east-1'):
    ec2_client = boto3.client('ec2', region_name=region)

    try:
        reserved_instances = ec2_client.describe_reserved_instances(Filters=[{'Name': 'state', 'Values': ['active']}])['ReservedInstances']
        total_reserved_instances = len(reserved_instances)

        reserved_instance_type_count = {}
        for reserved_instance in reserved_instances:
            instance_type = reserved_instance['InstanceType']
            lifecycle = 'reserved'  # Reserved instances lifecycle

            if instance_type not in reserved_instance_type_count:
                reserved_instance_type_count[instance_type] = 0
            reserved_instance_type_count[instance_type] += reserved_instance['InstanceCount']

        # Update Prometheus Gauges for Reserved Instances
        reserved_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_reserved_instances)
        for instance_type, count in reserved_instance_type_count.items():
            reserved_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type, lifecycle=lifecycle).set(count)

    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching Reserved Instance metrics: {e}")

# Call both metric collectors
def collect_all_ec2_metrics(region='us-east-1'):
    collect_ec2_metrics(region)
    collect_reserved_instance_metrics(region)
