from prometheus_client import Gauge, start_http_server
from utils.aws_context import ACCOUNT_ID
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus Gauges for RDS Instances
rds_instances_gauge = Gauge('aws_rds_instances_total', 'Total number of RDS instances', ['account_id', 'region'])
rds_instance_types_gauge = Gauge('aws_rds_instance_types', 'Number of RDS instances by type', ['account_id', 'region', 'instance_type'])
reserved_rds_instances_gauge = Gauge('aws_rds_reserved_instances_total', 'Total number of Reserved RDS Instances', ['account_id', 'region'])
reserved_rds_instance_types_gauge = Gauge('aws_rds_reserved_instance_types', 'Number of Reserved RDS Instances by type and state', ['account_id', 'region', 'instance_type', 'state'])

def collect_rds_metrics(region='us-east-1'):
    rds_client = boto3.client('rds', region_name=region)

    try:
        instances = rds_client.describe_db_instances()['DBInstances']
        total_instances = len(instances)
        instance_type_count = {}

        for instance in instances:
            instance_type = instance['DBInstanceClass']
            instance_type_count[instance_type] = instance_type_count.get(instance_type, 0) + 1

        rds_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_instances)
        for instance_type, count in instance_type_count.items():
            rds_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type).set(count)

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error fetching RDS metrics: {e}")

def collect_reserved_rds_instance_metrics(region='us-east-1'):
    rds_client = boto3.client('rds', region_name=region)

    try:
        reserved_instances = rds_client.describe_reserved_db_instances()['ReservedDBInstances']
        reserved_instance_type_count = {}

        for reserved_instance in reserved_instances:
            instance_type = reserved_instance['DBInstanceClass']
            state = reserved_instance['State']  # Fetch the state of the reserved instance
            count = reserved_instance['DBInstanceCount']

            # Initialize the counters for this instance type if not already initialized
            if instance_type not in reserved_instance_type_count:
                reserved_instance_type_count[instance_type] = {}

            # Increment the state-specific count
            if state not in reserved_instance_type_count[instance_type]:
                reserved_instance_type_count[instance_type][state] = 0
            reserved_instance_type_count[instance_type][state] += count

        # Update Prometheus Gauges for reserved RDS instances
        for instance_type, states in reserved_instance_type_count.items():
            for state, count in states.items():
                reserved_rds_instance_types_gauge.labels(
                    account_id=ACCOUNT_ID, 
                    region=region, 
                    instance_type=instance_type, 
                    state=state
                ).set(count)

    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching Reserved RDS Instance metrics: {e}")



def collect_all_rds_metrics(region='us-east-1'):
    collect_rds_metrics(region)
    collect_reserved_rds_instance_metrics(region)


