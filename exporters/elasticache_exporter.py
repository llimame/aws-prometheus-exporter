import boto3
from prometheus_client import Gauge
from utils.aws_context import ACCOUNT_ID

# Prometheus Gauges
elasticache_clusters_gauge = Gauge('aws_elasticache_clusters_total', 'Total number of ElastiCache clusters', ['account_id', 'region'])
elasticache_cluster_types_gauge = Gauge('aws_elasticache_cluster_types', 'Number of ElastiCache clusters by type', ['account_id', 'region', 'cluster_type'])

def collect_elasticache_metrics(region='us-east-1'):
    elasticache_client = boto3.client('elasticache', region_name=region)

    # Get cluster information
    clusters = elasticache_client.describe_cache_clusters()['CacheClusters']
    total_clusters = len(clusters)
    elasticache_clusters_gauge.labels(account_id=ACCOUNT_ID, region=region).set(total_clusters)

    cluster_type_count = {
        'redis': 0,
        'memcached': 0
    }
    for cluster in clusters:
        cluster_type = cluster['Engine'].lower()
        if cluster_type in cluster_type_count:
            cluster_type_count[cluster_type] += 1

    for cluster_type, count in cluster_type_count.items():
        elasticache_cluster_types_gauge.labels(account_id=ACCOUNT_ID, region=region, cluster_type=cluster_type).set(count)
