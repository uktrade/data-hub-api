import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datahub.core.queue import (
    BEAT_RUNNING_QUEUE,
    DataHubQueue,
)

with DataHubQueue() as queue:
    queue.work(BEAT_RUNNING_QUEUE)
