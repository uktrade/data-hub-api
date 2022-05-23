import os
from logging import getLogger

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings

logger = getLogger(__name__)

run_rq_exporter_command = f'rq-exporter --redis-url {settings.REDIS_BASE_URL}'
logger.info(run_rq_exporter_command)
os.system(run_rq_exporter_command)
