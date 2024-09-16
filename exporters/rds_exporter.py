import boto3
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID  # Importar o ID da conta

# Prometheus Gauges
rds_instances_gauge = Gauge('aws_rds_instances_total', 'Total number of RDS instances', ['account_id', 'region'])
rds_instance_types_gauge = Gauge('aws_rds_instance_types', 'Number of RDS instances by type', ['account_id', 'region', 'instance_type'])

# New Gauge for Reserved Instances
reserved_instance_types_gauge = Gauge('aws_rds_reserved_instance_types', 'Number of Reserved RDS Instances by type', ['account_id', 'region', 'instance_type', 'lifecycle'])

def collect_rds_metrics(regions=['us-east-1']):
    for region in regions:
        try:
            rds_client = boto3.client('rds', region_name=region)
            
            # Coletar instâncias padrão
            instances = rds_client.describe_db_instances()['DBInstances']
            rds_instances_gauge.labels(account_id=ACCOUNT_ID, region=region).set(len(instances))

            # Contagem de instâncias por tipo
            instance_type_count = {}
            for instance in instances:
                instance_type = instance['DBInstanceClass']
                instance_type_count[instance_type] = instance_type_count.get(instance_type, 0) + 1

            for instance_type, count in instance_type_count.items():
                rds_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type).set(count)

            # Coletar instâncias reservadas
            reserved_instances = rds_client.describe_reserved_db_instances()['ReservedDBInstances']

            reserved_instance_count = {}
            for reserved_instance in reserved_instances:
                instance_type = reserved_instance['DBInstanceClass']
                lifecycle = reserved_instance['State']  # Pode ser "active", "payment-pending", etc.
                key = (instance_type, lifecycle)

                reserved_instance_count[key] = reserved_instance_count.get(key, 0) + 1

            for (instance_type, lifecycle), count in reserved_instance_count.items():
                reserved_instance_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type, lifecycle=lifecycle).set(count)

        except Exception as e:
            print(f"Erro ao coletar métricas RDS para a região {region}: {str(e)}")
 