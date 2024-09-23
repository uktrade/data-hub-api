import importlib
import sys

from unittest.mock import patch

from django.conf import settings
from redis import Redis
from rq_scheduler import Scheduler

from datahub.core.queues.constants import EVERY_TEN_MINUTES


@patch('os.system')
class TestCompanyActivityIngestionTasks:
    def test_company_activity_ingestion_task_schedule(self, mock_system):
        """
        Test that a task is scheduled to check for new Company Activity data
        """
        # Import inside test to prevent the os.system call from running before the patch
        cron = importlib.import_module('cron-scheduler')
        cron.schedule_jobs()
        queue = 'long-running'

        scheduler = Scheduler(queue, connection=Redis.from_url(settings.REDIS_BASE_URL))
        scheduled_jobs = scheduler.get_jobs()
        ingestion_task = (
            'datahub.company_activity.tasks.ingest_company_activity.ingest_activity_data'
        )
        scheduled_job = [job for job in scheduled_jobs if job.func_name == ingestion_task][0]
        assert scheduled_job.func_name == ingestion_task
        assert scheduled_job.meta['cron_string'] == EVERY_TEN_MINUTES

        # Prevents the scheduler loop from running after tests finish by unloading the module again
        sys.modules.pop('cron-scheduler')
