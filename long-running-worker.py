import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datahub.core.queue import (
    DataHubQueue,
    LONG_RUNNING_QUEUE,
)

with DataHubQueue() as queue:
    queue.work(LONG_RUNNING_QUEUE)
