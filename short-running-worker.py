import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datahub.core.queues.scheduler import (
    DataHubScheduler,
    SHORT_RUNNING_QUEUE,
)

with DataHubScheduler() as queue:
    queue.work(SHORT_RUNNING_QUEUE, with_scheduler=True)
