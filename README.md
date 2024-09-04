# AWS Metrics Exporter for Prometheus

AWS Metrics Exporter is a Python application that collects and exposes metrics from AWS services for Prometheus monitoring. The tool supports metrics collection from AWS EC2, RDS, and ElastiCache.

## Features

- EC2 Metrics: Total number of EC2 instances and breakdown by instance type.
- RDS Metrics: Total number of RDS instances.
- ElastiCache Metrics: Total number of ElastiCache clusters and breakdown by cluster type.

## Getting Started

### Prerequisites

- Python 3.9+
- boto3 for AWS SDK
- prometheus_client for Prometheus metrics
- AWS credentials with permissions for EC2, RDS, and ElastiCache

### Installation
```
#Clone the repository:
git clone https://github.com/yourusername/aws-metrics-exporter.git
cd aws-metrics-exporter

#Install dependencies:
pip install -r requirements.txt

#Set up your AWS credentials using environment variables or AWS CLI configuration:
export AWS_ACCESS_KEY_ID='your-access-key-id'
export AWS_SECRET_ACCESS_KEY='your-secret-access-key'
```
### Configuration
```
Edit config/config.yaml to configure collectors and Prometheus settings:
collectors:
  iam: true
  rds: true
  ec2: true
  elasticache: true

settings:
  prometheus_port: 8000
  regions:
    - us-east-1
    - us-west-2
```

### Usage
```
#Run the exporter with:
python main.py
```

The exporter will start on the port specified in the configuration file (default: 9090).

### Metrics

- EC2 Metrics:
  - aws_ec2_instances_total: Total number of EC2 instances, labeled with account_id.
  - aws_ec2_instance_types: Number of EC2 instances by type, labeled with account_id and instance_type.

- RDS Metrics:
  - aws_rds_instances_total: Total number of RDS instances, labeled with account_id and region.

- ElastiCache Metrics:
  - aws_elasticache_clusters_total: Total number of ElastiCache clusters, labeled with account_id and region.
  - aws_elasticache_cluster_types: Number of ElastiCache clusters by type (Redis or Memcached), labeled with account_id, region, and cluster_type.

### Contributing
Feel free to contribute by opening issues or submitting pull requests.

### License
This project is licensed under the MIT License. See the LICENSE file for details.
