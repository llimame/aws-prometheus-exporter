from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Prometheus Gauges for RDS Instances
rds_instances_gauge = Gauge('aws_rds_instances_total', 'Total number of RDS instances', ['account_id', 'region'])
rds_instance_types_gauge = Gauge('aws_rds_instance_types', 'Number of RDS instances by type', ['account_id', 'region', 'instance_type'])
reserved_rds_instances_gauge = Gauge('aws_rds_reserved_instances_total', 'Total number of Reserved RDS Instances', ['account_id', 'region'])
reserved_rds_instance_types_gauge = Gauge('aws_rds_reserved_instance_types', 'Number of Reserved RDS Instances by type and lifecycle', ['account_id', 'region', 'instance_type', 'lifecycle'])

def collect_rds_metrics(region='us-east-1'):
    rds_client = boto3.client('rds', region_name=region)

    try:
        instances = rds_client.describe_db_instances()['DBInstances']
        total_instances = len(instances)
        instance_type_count = {}

        # Collect metrics for RDS instances
        for instance in instances:
            instance_type = instance['DBInstanceClass']
            if instance_type not in instance_type_count:
                instance_type_count[instance_type] = 0
            instance_type_count[instance_type] += 1

        # Update Prometheus Gauges for RDS instances
        rds_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_instances)
        for instance_type, count in instance_type_count.items():
            rds_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type).set(count)

    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching RDS metrics: {e}")


def collect_reserved_rds_instance_metrics(region='us-east-1'):
    rds_client = boto3.client('rds', region_name=region)

    try:
        # Fetch reserved RDS instances
        reserved_instances = rds_client.describe_reserved_db_instances(Filters=[{'Name': 'State', 'Values': ['active']}])['ReservedDBInstances']
        total_reserved_instances = len(reserved_instances)
        reserved_instance_type_count = {}

        # Collect reserved RDS instance data by type and lifecycle
        for reserved_instance in reserved_instances:
            instance_type = reserved_instance['DBInstanceClass']
            lifecycle = 'reserved'  # Reserved instances lifecycle

            if instance_type not in reserved_instance_type_count:
                reserved_instance_type_count[instance_type] = 0
            reserved_instance_type_count[instance_type] += reserved_instance['DBInstanceCount']

        # Update Prometheus Gauges for reserved RDS instances
        reserved_rds_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_reserved_instances)
        for instance_type, count in reserved_instance_type_count.items():
            reserved_rds_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type, lifecycle=lifecycle).set(count)

    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching Reserved RDS Instance metrics: {e}")


# Function to collect all RDS metrics
def collect_all_rds_metrics(region='us-east-1'):
    collect_rds_metrics(region)
    collect_reserved_rds_instance_metrics(region)
