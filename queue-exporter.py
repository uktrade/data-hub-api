import os
from logging import getLogger

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()


logger = getLogger(__name__)

"""
REMARKS: This space is for overriding the default environment variables by
    setting https://github.com/mdawar/rq-exporter#configuration
"""
run_rq_exporter_command = 'rq-exporter'
logger.info(run_rq_exporter_command)
os.system(run_rq_exporter_command)
