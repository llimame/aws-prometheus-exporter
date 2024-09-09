from prometheus_client import start_http_server
import time
from exporters.iam_exporter import collect_iam_metrics
from exporters.rds_exporter import collect_rds_metrics
from exporters.ec2_exporter import collect_all_ec2_metrics
from exporters.elasticache_exporter import collect_elasticache_metrics
from config.config import config, PROMETHEUS_PORT

from config.config import config, PROMETHEUS_PORT, REGIONS

def collect_metrics():
    for region in REGIONS:
        if config['collectors'].get('iam', False):
            collect_iam_metrics()
        if config['collectors'].get('rds', False):
            collect_rds_metrics(region)
        if config['collectors'].get('ec2', False):
            collect_all_ec2_metrics(region)
        if config['collectors'].get('elasticache', False):
            collect_elasticache_metrics(region)

if __name__ == "__main__":
    start_http_server(PROMETHEUS_PORT)
    print(f"Prometheus exporter started on port {PROMETHEUS_PORT}")

    while True:
        collect_metrics()
        time.sleep(3600)
