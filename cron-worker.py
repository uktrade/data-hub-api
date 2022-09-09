import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datahub.core.queues.queue import (
    DataHubQueue,
    CRON_QUEUE,
)

with DataHubQueue() as queue:
    queue.work(CRON_QUEUE)
