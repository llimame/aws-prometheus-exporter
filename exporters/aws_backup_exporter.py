#!/usr/bin/env python3
from prometheus_client import Gauge, start_http_server
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError
import time
from datetime import datetime, timezone, timedelta

# ==========================
# Logging
# ==========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ==========================
# Prometheus Gauges
# ==========================
backup_jobs_total = Gauge(
    'aws_backup_jobs_total',
    'Total number of AWS Backup jobs (últimas 24h)',
    ['account_id', 'region']
)
backup_jobs_state = Gauge(
    'aws_backup_jobs_state_total',
    'Number of AWS Backup jobs by state (últimas 24h)',
    ['account_id', 'region', 'state']
)
backup_jobs_resource = Gauge(
    'aws_backup_jobs_resource_total',
    'Number of AWS Backup jobs grouped by resource (últimas 24h)',
    ['account_id', 'region', 'state', 'resource_type', 'resource_name']
)
backup_last_backup_timestamp = Gauge(
    'aws_backup_last_backup_timestamp',
    'Unix timestamp of the last backup job per region (últimas 24h)',
    ['account_id', 'region']
)
backup_last_backup_timestamp_resource = Gauge(
    'aws_backup_last_backup_timestamp_resource',
    'Unix timestamp of the last backup job per resource (últimas 24h)',
    ['account_id', 'region', 'resource_type', 'resource_name']
)

# ==========================
# AWS Setup
# ==========================
ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']


# ==========================
# Helpers
# ==========================
def list_backup_jobs_last_24h(client):
    """Lista apenas jobs criados nas últimas 24 horas."""
    jobs = []
    next_token = None

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=24)

    while True:
        kwargs = {
            'MaxResults': 1000,
            'ByCreatedAfter': start_time,
            'ByCreatedBefore': now
        }
        if next_token:
            kwargs['NextToken'] = next_token
        response = client.list_backup_jobs(**kwargs)
        jobs.extend(response.get('BackupJobs', []))
        next_token = response.get('NextToken')
        if not next_token:
            break
    return jobs


def parse_resource_info(resource_arn):
    """Extrai tipo e nome do recurso a partir do ARN."""
    try:
        arn_parts = resource_arn.split(':', 5)
        service = arn_parts[2]
        resource_part = arn_parts[5]
        if '/' in resource_part:
            resource_type, resource_name = resource_part.split('/', 1)
        else:
            resource_type, resource_name = "unknown", resource_part
        return service, resource_name
    except Exception:
        return "unknown", resource_arn


# ==========================
# Coleta principal
# ==========================
def collect_backup_metrics(region='us-east-1'):
    client = boto3.client('backup', region_name=region)

    # Limpa métricas antigas antes da atualização
    backup_jobs_state.clear()
    backup_jobs_total.clear()
    backup_jobs_resource.clear()
    backup_last_backup_timestamp.clear()
    backup_last_backup_timestamp_resource.clear()

    try:
        jobs = list_backup_jobs_last_24h(client)
        total_jobs = len(jobs)
        state_count = {}
        resource_count = {}

        latest_job = None
        latest_per_resource = {}

        for job in jobs:
            state = job['State']
            creation = job['CreationDate']

            # Contagem por estado
            state_count[state] = state_count.get(state, 0) + 1

            # Contagem por recurso
            resource_type, resource_name = parse_resource_info(job.get('ResourceArn', 'unknown'))
            key = (state, resource_type, resource_name)
            resource_count[key] = resource_count.get(key, 0) + 1

            # Últimos backups
            if not latest_job or creation > latest_job['CreationDate']:
                latest_job = job

            res_key = (resource_type, resource_name)
            if res_key not in latest_per_resource or creation > latest_per_resource[res_key]['CreationDate']:
                latest_per_resource[res_key] = job

        # Atualiza métricas Prometheus
        backup_jobs_total.labels(account_id=ACCOUNT_ID, region=region).set(total_jobs)

        for state, count in state_count.items():
            backup_jobs_state.labels(account_id=ACCOUNT_ID, region=region, state=state).set(count)

        for (state, resource_type, resource_name), count in resource_count.items():
            backup_jobs_resource.labels(
                account_id=ACCOUNT_ID,
                region=region,
                state=state,
                resource_type=resource_type,
                resource_name=resource_name
            ).set(count)

        # Últimos timestamps
        if latest_job:
            backup_last_backup_timestamp.labels(account_id=ACCOUNT_ID, region=region).set(
                latest_job['CreationDate'].timestamp()
            )

        for (resource_type, resource_name), job in latest_per_resource.items():
            backup_last_backup_timestamp_resource.labels(
                account_id=ACCOUNT_ID,
                region=region,
                resource_type=resource_type,
                resource_name=resource_name
            ).set(job['CreationDate'].timestamp())

        failed = state_count.get("FAILED", 0)
        completed = state_count.get("COMPLETED", 0)
        logger.info(f"[{region}] Jobs nas últimas 24h: {total_jobs}, Completed: {completed}, Failed: {failed}")

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Erro AWS Backup na região {region}: {e}")
    except Exception as e:
        logger.exception(f"Erro inesperado na região {region}: {e}")

