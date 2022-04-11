import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datahub.core.queue import DataHubQueue

with DataHubQueue() as queue:
    queue.work('short-running', 'long-running')
