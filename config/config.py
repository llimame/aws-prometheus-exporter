import yaml
import os

def load_config():
    with open("config/config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()

# Access the settings like this
PROMETHEUS_PORT = config['settings']['prometheus_port']
REGIONS = config['settings']['regions']

# Acessa as credenciais da AWS a partir das variáveis de ambiente
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise EnvironmentError("AWS credentials are not set in the environment variables.")