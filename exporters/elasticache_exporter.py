import boto3
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID

# Prometheus Gauges
elasticache_cluster_types_gauge = Gauge('aws_elasticache_cluster_types', 'Number of ElastiCache clusters by type and instance type', ['account_id', 'region', 'cluster_type', 'instance_type'])
reserved_cache_node_types_gauge = Gauge('aws_elasticache_reserved_node_types', 'Number of reserved ElastiCache nodes by instance type', ['account_id', 'region', 'instance_type'])

def collect_elasticache_metrics(region='us-east-1'):
    elasticache_client = boto3.client('elasticache', region_name=region)

    # Get cluster information
    clusters = elasticache_client.describe_cache_clusters()['CacheClusters']
    
    # Count clusters by type and instance type
    cluster_type_count = {}
    for cluster in clusters:
        cluster_type = cluster['Engine'].lower()
        instance_type = cluster['CacheNodeType']
        key = (cluster_type, instance_type)
        if key not in cluster_type_count:
            cluster_type_count[key] = 0
        cluster_type_count[key] += 1

    for (cluster_type, instance_type), count in cluster_type_count.items():
        elasticache_cluster_types_gauge.labels(account_id=ACCOUNT_ID, region=region, cluster_type=cluster_type, instance_type=instance_type).set(count)

    # Get reserved instance information
    reserved_nodes = elasticache_client.describe_reserved_cache_nodes()['ReservedCacheNodes']

    # Count only active reserved instances by instance type
    reserved_node_type_count = {}
    for node in reserved_nodes:
        if node['State'] == 'active':  # Only count if the status is 'active'
            instance_type = node['CacheNodeType']
            if instance_type not in reserved_node_type_count:
                reserved_node_type_count[instance_type] = 0
            reserved_node_type_count[instance_type] += 1

    for instance_type, count in reserved_node_type_count.items():
        reserved_cache_node_types_gauge.labels(account_id=ACCOUNT_ID, region=region, instance_type=instance_type).set(count)
