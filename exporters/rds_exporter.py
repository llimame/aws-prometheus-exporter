import boto3
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID  # Importar o ID da conta

# Prometheus Gauges
rds_instances_gauge = Gauge('aws_rds_instances_total', 'Total number of RDS instances', ['account_id', 'region'])
rds_instance_types_gauge = Gauge('aws_rds_instance_types', 'Number of RDS instances by type', ['account_id', 'region', 'instance_type'])

def collect_rds_metrics(region='us-east-1'):
    rds_client = boto3.client('rds', region_name=region)

    instances = rds_client.describe_db_instances()['DBInstances']
    rds_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(len(instances))

    instance_type_count = {}
    for instance in instances:
        instance_type = instance['DBInstanceClass']
        if instance_type not in instance_type_count:
            instance_type_count[instance_type] = 0
        instance_type_count[instance_type] += 1

    for instance_type, count in instance_type_count.items():
        rds_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type).set(count)
