import logging

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from django.conf import settings
from moto import mock_aws
from redis import Redis
from rq import Queue, Worker
from rq.job import Job

from datahub.company_activity.models import IngestedFile
from datahub.company_activity.tests.factories import CompanyActivityIngestedFileFactory
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import DataHubScheduler
from datahub.investment_lead.serializers import (
    CreateEYBLeadMarketingSerializer,
    CreateEYBLeadTriageSerializer,
    CreateEYBLeadUserSerializer,
)
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BUCKET,
    REGION,
)
from datahub.investment_lead.tasks.ingest_eyb_marketing import (
    EYBMarketingDataIngestionTask,
    ingest_eyb_marketing_data,
    ingest_eyb_marketing_file,
    MARKETING_PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    EYBTriageDataIngestionTask,
    ingest_eyb_triage_data,
    ingest_eyb_triage_file,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    EYBUserDataIngestionTask,
    ingest_eyb_user_data,
    ingest_eyb_user_file,
    USER_PREFIX,
)
from datahub.investment_lead.test.test_tasks.utils import (
    setup_s3_bucket,
    setup_s3_client,
)
from datahub.investment_lead.test.utils import assert_datetimes


pytestmark = pytest.mark.django_db


def get_test_file_paths(prefix):
    file_names = [
        '1.jsonl.gz',
        '2.jsonl.gz',
        '3.jsonl.gz',
    ]
    return [f'{prefix}{name}' for name in file_names]


class TestEYBCommonFileIngestionTasks:
    @pytest.mark.parametrize(
        'prefix, ingest_file_task_function',
        [
            (TRIAGE_PREFIX, ingest_eyb_triage_file),
            (USER_PREFIX, ingest_eyb_user_file),
            (MARKETING_PREFIX, ingest_eyb_marketing_file),
        ],
    )
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_not_queued_for_already_ingested_file(
        self, mock, prefix, ingest_file_task_function, caplog,
    ):
        file_paths = get_test_file_paths(prefix)
        ingested_file_path = file_paths[-1]
        setup_s3_bucket(BUCKET, file_paths)
        for file_path in file_paths:
            IngestedFile.objects.create(filepath=file_path)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count

        with caplog.at_level(logging.INFO):
            ingest_file_task_function()
            assert f'{ingested_file_path} has already been ingested' in caplog.text
        assert rq_queue.count == initial_job_count

    @pytest.mark.parametrize(
        'prefix, ingest_data_task_function, ingest_file_task_function',
        [
            (TRIAGE_PREFIX, ingest_eyb_triage_data, ingest_eyb_triage_file),
            (USER_PREFIX, ingest_eyb_user_data, ingest_eyb_user_file),
            (MARKETING_PREFIX, ingest_eyb_marketing_data, ingest_eyb_marketing_file),
        ],
    )
    @pytest.mark.django_db
    # Patch so that we can simulate a job on the queue rather than having it run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @mock_aws
    def test_ingestion_job_is_not_queued_again_when_already_on_queue(
        self, mock, prefix, ingest_data_task_function, ingest_file_task_function, caplog,
    ):
        """
        Test that when, the job has run and queued an ingestion job for a file
        but that child job hasn't completed yet, this job does not queue a duplicate
        when running again
        """
        file_paths = get_test_file_paths(prefix)
        new_file_path = file_paths[-1]
        setup_s3_bucket(BUCKET, file_paths)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        job_scheduler(
            function=ingest_data_task_function,
            function_kwargs={'bucket': BUCKET, 'file': new_file_path},
            queue_name='long-running',
            description='Ingest EYB data',
        )
        initial_job_count = rq_queue.count
        with caplog.at_level(logging.INFO):
            ingest_file_task_function()
            assert f'{new_file_path} has already been queued for ingestion' in caplog.text
        assert rq_queue.count == initial_job_count

    @pytest.mark.parametrize(
        'prefix, ingest_file_task_function, job_function_name',
        [
            (
                TRIAGE_PREFIX,
                ingest_eyb_triage_file,
                'datahub.investment_lead.tasks.ingest_eyb_triage.ingest_eyb_triage_data',
            ),
            (
                USER_PREFIX,
                ingest_eyb_user_file,
                'datahub.investment_lead.tasks.ingest_eyb_user.ingest_eyb_user_data',
            ),
            (
                MARKETING_PREFIX,
                ingest_eyb_marketing_file,
                'datahub.investment_lead.tasks.ingest_eyb_marketing.ingest_eyb_marketing_data',
            ),
        ],
    )
    @pytest.mark.django_db
    # Patch so that we can test the job is queued, rather than having it be run instantly
    @patch(
        'datahub.core.queues.job_scheduler.DataHubScheduler',
        return_value=DataHubScheduler(is_async=True),
    )
    @patch('datahub.investment_lead.tasks.ingest_eyb_common.Worker')
    @mock_aws
    def test_triage_ingestion_job_not_queued_when_job_is_already_running(
        self, mock_worker, mock_scheduler, prefix, job_function_name, ingest_file_task_function,
    ):
        """Test that we don't queue a job to ingest a file when one is already running for it."""
        file_paths = get_test_file_paths(prefix)
        new_file_path = file_paths[-1]
        setup_s3_bucket(BUCKET, file_paths)

        redis = Redis.from_url(settings.REDIS_BASE_URL)
        rq_queue = Queue('long-running', connection=redis)
        rq_queue.empty()
        initial_job_count = rq_queue.count
        mock_job = Job.create(job_function_name, kwargs={'file': new_file_path}, connection=redis)
        mock_worker_instance = Worker(['long-running'], connection=redis)
        mock_worker_instance.get_current_job = MagicMock(return_value=mock_job)
        mock_worker.all.return_value = [mock_worker_instance]

        ingest_file_task_function()
        assert rq_queue.count == initial_job_count


class TestEYBCommonDataIngestionTasks:
    @pytest.mark.parametrize(
        'ingest_data_task_class, serializer_class',
        [
            (EYBTriageDataIngestionTask, CreateEYBLeadTriageSerializer),
            (EYBUserDataIngestionTask, CreateEYBLeadUserSerializer),
            (EYBMarketingDataIngestionTask, CreateEYBLeadMarketingSerializer),
        ],
    )
    def test_get_last_ingestion_datetime_of_data(self, ingest_data_task_class, serializer_class):
        """Test that the most recent file is ingested, for the given file path.

        CompanyActivityIngestedFile model will record all files that have been ingested.
        We want to ensure that the job gets the last ingestion datetime for the specific
        file path, thus ignoring more recently ingested files containing other datasets.
        """
        target_filepath_prefix = 'data-flow/eyb-pipeline/'
        other_filepath_prefix = 'data-flow/other-pipeline/'

        now = datetime.now(tz=timezone.utc)
        yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
        day_before_yesterday = datetime.now(tz=timezone.utc) - timedelta(days=2)

        CompanyActivityIngestedFileFactory(
            filepath=target_filepath_prefix + '1.jsonl.gz',
            created_on=day_before_yesterday,
        )
        most_recently_ingested_target_file = CompanyActivityIngestedFileFactory(
            filepath=target_filepath_prefix + '2.jsonl.gz',
            created_on=yesterday,
        )
        CompanyActivityIngestedFileFactory(
            filepath=other_filepath_prefix + '1.jsonl.gz',
            created_on=now,
        )
        most_recent_target_file_ingestion_datetime = ingest_data_task_class(
            serializer_class=serializer_class,
            prefix=target_filepath_prefix,
        )._last_ingestion_datetime

        assert_datetimes(
            most_recent_target_file_ingestion_datetime,
            most_recently_ingested_target_file.created_on,
        )

    @pytest.mark.parametrize(
        'ingest_data_task_function',
        [
            (ingest_eyb_triage_data),
            (ingest_eyb_user_data),
            (ingest_eyb_marketing_data),
        ],
    )
    @mock_aws
    def test_an_exception_is_raised_when_file_does_not_exist(
        self, ingest_data_task_function,
    ):
        mock_s3_client = setup_s3_client()
        mock_s3_client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={'LocationConstraint': REGION},
        )
        file_path = 'a/file/that/does/not/exist.jsonl.gz'
        with pytest.raises(Exception) as e:
            ingest_data_task_function(BUCKET, file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = f"key: '{file_path}'"
        assert expected in exception
