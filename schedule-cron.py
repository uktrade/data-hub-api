import os
import pprint

import django

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings


def cron_test_function():
    pprint('######################')
    pprint('testing cron successful')

# You can also instantiate a Scheduler using an RQ Queue
queue = Queue('test-queue', connection=Redis.from_url('redis://redis:6379'))
scheduler = Scheduler(queue=queue)

# Puts a job into the scheduler. The API is similar to RQ except that it
# takes a datetime object as first argument. So for example to schedule a
# job to run on Jan 1st 2020 we do:
scheduler.cron('* * * * *', cron_test_function, repeat=10)# Date time should be in UTC
