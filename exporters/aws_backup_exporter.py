from prometheus_client import Gauge, start_http_server
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError
import time
from datetime import datetime, timedelta, timezone

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus Gauges
backup_jobs_total = Gauge('aws_backup_jobs_total', 'Total number of AWS Backup jobs', ['account_id', 'region'])
backup_jobs_state = Gauge('aws_backup_jobs_state_total', 'Number of AWS Backup jobs by state', ['account_id', 'region', 'state'])

backup_jobs_last24h_total = Gauge('aws_backup_jobs_last24h_total', 'Total number of AWS Backup jobs in the last 24h', ['account_id', 'region'])
backup_jobs_last24h_state = Gauge('aws_backup_jobs_last24h_state_total', 'Number of AWS Backup jobs by state in last 24h', ['account_id', 'region', 'state'])

backup_jobs_resource = Gauge(
    'aws_backup_jobs_resource_total',
    'Number of AWS Backup jobs grouped by resource',
    ['account_id', 'region', 'state', 'resource_type', 'resource_name']
)

# Gauges for last backup date
backup_last_backup_timestamp = Gauge(
    'aws_backup_last_backup_timestamp',
    'Unix timestamp of the last backup job per region',
    ['account_id', 'region']
)

backup_last_backup_timestamp_resource = Gauge(
    'aws_backup_last_backup_timestamp_resource',
    'Unix timestamp of the last backup job per resource',
    ['account_id', 'region', 'resource_type', 'resource_name']
)

ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']

def list_all_backup_jobs(client):
    jobs = []
    next_token = None
    while True:
        kwargs = {'MaxResults': 1000}
        if next_token:
            kwargs['NextToken'] = next_token
        response = client.list_backup_jobs(**kwargs)
        jobs.extend(response['BackupJobs'])
        next_token = response.get('NextToken')
        if not next_token:
            break
    return jobs

def parse_resource_info(resource_arn):
    try:
        parts = resource_arn.split(':', 5)
        resource_type = parts[2]  # service
        resource_name = parts[-1].split('/')[-1].split(':')[-1]
        return resource_type, resource_name
    except Exception:
        return "unknown", resource_arn

def collect_backup_metrics(region='us-east-1'):
    client = boto3.client('backup', region_name=region)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    try:
        jobs = list_all_backup_jobs(client)
        total_jobs = len(jobs)
        state_count = {}
        last24h_count = {}
        resource_count = {}

        latest_job = None
        latest_per_resource = {}

        for job in jobs:
            state = job['State']
            creation = job['CreationDate']

            # state counters (all time)
            state_count[state] = state_count.get(state, 0) + 1

            # resource counters
            resource_type, resource_name = parse_resource_info(job.get('ResourceArn', 'unknown'))
            key = (state, resource_type, resource_name)
            resource_count[key] = resource_count.get(key, 0) + 1

            # jobs last 24h
            if creation >= cutoff:
                last24h_count[state] = last24h_count.get(state, 0) + 1

            # track latest job overall
            if not latest_job or creation > latest_job['CreationDate']:
                latest_job = job

            # track latest job per resource
            res_key = (resource_type, resource_name)
            if res_key not in latest_per_resource or creation > latest_per_resource[res_key]['CreationDate']:
                latest_per_resource[res_key] = job

        # Update Prometheus (job counts)
        backup_jobs_total.labels(account_id=ACCOUNT_ID, region=region).set(total_jobs)
        for state, count in state_count.items():
            backup_jobs_state.labels(account_id=ACCOUNT_ID, region=region, state=state).set(count)

        backup_jobs_last24h_total.labels(account_id=ACCOUNT_ID, region=region).set(sum(last24h_count.values()))
        for state, count in last24h_count.items():
            backup_jobs_last24h_state.labels(account_id=ACCOUNT_ID, region=region, state=state).set(count)

        for (state, resource_type, resource_name), count in resource_count.items():
            backup_jobs_resource.labels(
                account_id=ACCOUNT_ID,
                region=region,
                state=state,
                resource_type=resource_type,
                resource_name=resource_name
            ).set(count)

        # Last backup timestamp (region-level)
        if latest_job:
            backup_last_backup_timestamp.labels(account_id=ACCOUNT_ID, region=region).set(
                latest_job['CreationDate'].timestamp()
            )

        # Last backup timestamp (resource-level)
        for (resource_type, resource_name), job in latest_per_resource.items():
            backup_last_backup_timestamp_resource.labels(
                account_id=ACCOUNT_ID,
                region=region,
                resource_type=resource_type,
                resource_name=resource_name
            ).set(job['CreationDate'].timestamp())

        logger.info(f"[{region}] Total: {total_jobs}, Last24h: {sum(last24h_count.values())}, LastJob: {latest_job['State'] if latest_job else 'N/A'}")

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Erro ao coletar métricas do AWS Backup na região {region}: {e}")

def collect_all_regions(regions):
    for region in regions:
        try:
            collect_backup_metrics(region)
        except Exception as e:
            logger.error(f"Erro inesperado na região {region}: {e}")

if __name__ == '__main__':
    start_http_server(8000)
    regions = ['us-east-1', 'us-west-2']  # customize
    while True:
        collect_all_regions(regions)
        time.sleep(300)  # 5 min
