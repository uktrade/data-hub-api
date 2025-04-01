import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datahub.core.queues.scheduler import (
    LONG_RUNNING_QUEUE,
    DataHubScheduler,
)

with DataHubScheduler() as queue:
    queue.work(LONG_RUNNING_QUEUE, with_scheduler=True)
