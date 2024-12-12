import logging

from datetime import (
    datetime,
    timezone,
)
from unittest import mock
from uuid import uuid4

import pytest

from moto import mock_aws
from rq.job import Job

from datahub.ingest.constants import (
    TEST_OBJECT_KEY,
    TEST_PREFIX,
)
from datahub.ingest.models import IngestedObject
from datahub.ingest.tasks import (
    base_ingestion_task,
    BaseObjectIdentificationTask,
    BaseObjectIngestionTask,
    QueueChecker,
    S3ObjectProcessor,
)
from datahub.ingest.utils import (
    compressed_json_faker,
    upload_objects_to_s3,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_redis():
    with mock.patch('datahub.ingest.tasks.Redis') as mock_redis:
        yield mock_redis


@pytest.fixture
def mock_queue():
    with mock.patch('datahub.ingest.tasks.Queue') as mock_queue:
        yield mock_queue


@pytest.fixture
def mock_worker():
    with mock.patch('datahub.ingest.tasks.Worker') as mock_worker:
        yield mock_worker


@pytest.fixture
def mock_scheduler():
    with mock.patch('datahub.ingest.tasks.job_scheduler') as mock_scheduler:
        yield mock_scheduler


class TestQueueChecker:

    def test_match_job_returns_true_if_job_matches(self, mock_redis):
        queue_checker = QueueChecker('test-queue')
        job = Job.create(
            func=base_ingestion_task,
            kwargs={'object_key': TEST_OBJECT_KEY},
            connection=mock_redis,
        )
        assert queue_checker.match_job(
            job=job,
            ingestion_task_function=base_ingestion_task,
            object_key=TEST_OBJECT_KEY,
        )

    def test_match_job_returns_false_if_job_does_not_match(self, mock_redis):
        queue_checker = QueueChecker('test-queue')
        job = Job.create(
            func=base_ingestion_task,
            kwargs={'object_key': 'different.json'},
            connection=mock_redis,
        )
        assert not queue_checker.match_job(
            job=job,
            ingestion_task_function=base_ingestion_task,
            object_key=TEST_OBJECT_KEY,
        )

    def test_is_job_queued_returns_true_if_job_is_queued(self, mock_redis, mock_queue):
        queue_checker = QueueChecker('test-queue')
        job = Job.create(
            func=base_ingestion_task,
            kwargs={'object_key': TEST_OBJECT_KEY},
            connection=mock_redis,
        )
        mock_queue.return_value.jobs = [job]
        assert queue_checker.is_job_queued(
            ingestion_task_function=base_ingestion_task,
            object_key=TEST_OBJECT_KEY,
        )

    def test_is_job_queued_returns_false_if_job_is_not_queued(self, mock_queue):
        queue_checker = QueueChecker('test-queue')
        mock_queue.return_value.jobs = []
        assert not queue_checker.is_job_queued(
            ingestion_task_function=base_ingestion_task,
            object_key=TEST_OBJECT_KEY,
        )

    def test_is_job_running_returns_true_if_job_is_running(
        self, mock_redis, mock_queue, mock_worker,
    ):
        queue_checker = QueueChecker('test-queue')
        job = Job.create(
            func=base_ingestion_task,
            kwargs={'object_key': TEST_OBJECT_KEY},
            connection=mock_redis,
        )
        mock_queue.return_value.jobs = []
        mock_worker.all.return_value = [mock.Mock(get_current_job=lambda: job)]
        assert queue_checker.is_job_running(
            ingestion_task_function=base_ingestion_task,
            object_key=TEST_OBJECT_KEY,
        )

    def test_is_job_running_returns_false_if_job_is_not_running(
        self, mock_queue, mock_worker,
    ):
        queue_checker = QueueChecker('test-queue')
        mock_queue.return_value.jobs = []
        mock_worker.all.return_value = [mock.Mock(get_current_job=lambda: None)]
        assert not queue_checker.is_job_running(
            ingestion_task_function=base_ingestion_task,
            object_key=TEST_OBJECT_KEY,
        )


@mock_aws
class TestBaseObjectIdentificationTask:

    @pytest.fixture
    def identification_task(self):
        return BaseObjectIdentificationTask(prefix=TEST_PREFIX)

    def test_identify_new_objects_when_no_objects_found(
        self, identification_task, mock_scheduler, caplog,
    ):
        with (
            mock.patch.object(S3ObjectProcessor, 'get_most_recent_object_key', return_value=None),
            caplog.at_level(logging.INFO),
        ):
            identification_task.identify_new_objects(base_ingestion_task)
            assert 'No objects found' in caplog.text
        mock_scheduler.assert_not_called()

    def test_identify_new_objects_when_job_already_queued(
        self,
        identification_task,
        mock_scheduler,
        caplog,
    ):
        with (
            mock.patch.object(
                S3ObjectProcessor, 'get_most_recent_object_key', return_value=TEST_OBJECT_KEY,
            ),
            mock.patch.object(QueueChecker, 'is_job_queued', return_value=True),
            caplog.at_level(logging.INFO),
        ):
            identification_task.identify_new_objects(base_ingestion_task)
            assert f'{TEST_OBJECT_KEY} has already been queued for ingestion' in caplog.text
        mock_scheduler.assert_not_called()

    def test_identify_new_objects_when_job_is_running(
        self,
        identification_task,
        mock_scheduler,
        caplog,
    ):
        with (
            mock.patch.object(
                S3ObjectProcessor, 'get_most_recent_object_key', return_value=TEST_OBJECT_KEY,
            ),
            mock.patch.object(QueueChecker, 'is_job_running', return_value=True),
            caplog.at_level(logging.INFO),
        ):
            identification_task.identify_new_objects(base_ingestion_task)
            assert f'{TEST_OBJECT_KEY} is currently being ingested' in caplog.text
        mock_scheduler.assert_not_called()

    def test_identify_new_objects_when_object_already_ingested(
        self, identification_task, mock_scheduler, caplog,
    ):
        with (
            mock.patch.object(
                S3ObjectProcessor, 'get_most_recent_object_key', return_value=TEST_OBJECT_KEY,
            ),
            mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=True),
            caplog.at_level(logging.INFO),
        ):
            identification_task.identify_new_objects(base_ingestion_task)
            assert f'{TEST_OBJECT_KEY} has already been ingested' in caplog.text
        mock_scheduler.assert_not_called()

    def test_identify_new_objects_schedules_ingestion_task(
        self, identification_task, mock_scheduler, caplog,
    ):
        with (
            mock.patch.object(
                S3ObjectProcessor, 'get_most_recent_object_key', return_value=TEST_OBJECT_KEY,
            ),
            mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=False),
            caplog.at_level(logging.INFO),
        ):
            identification_task.identify_new_objects(base_ingestion_task)
            assert f'Scheduled ingestion of {TEST_OBJECT_KEY}' in caplog.text
        mock_scheduler.assert_called_once_with(
            function=base_ingestion_task,
            function_kwargs={
                'object_key': TEST_OBJECT_KEY,
                's3_processor': identification_task.s3_processor,
            },
            queue_name='long-running',
            description=f'Ingest {TEST_OBJECT_KEY}',
        )


@mock_aws
class TestBaseObjectIngestionTask:

    @pytest.fixture
    def ingestion_task(self, s3_object_processor):
        return BaseObjectIngestionTask(
            object_key=TEST_OBJECT_KEY,
            s3_processor=s3_object_processor,
        )

    def test_ingest_task_raises_error(self, caplog, s3_object_processor):
        with (
            pytest.raises(Exception),
            caplog.at_level(logging.INFO),
        ):
            base_ingestion_task(TEST_OBJECT_KEY, s3_object_processor)
            assert 'Base ingestion task started...' in caplog.text
            assert f'An error occurred trying to process {TEST_OBJECT_KEY}' in caplog.text

    def test_ingest_object_raises_not_implemented_error(
        self, s3_object_processor, caplog, ingestion_task,
    ):
        """Test the process_record method's NotImplementedError is propagated."""
        object_definition = (TEST_OBJECT_KEY, compressed_json_faker([
            {'modified': '2024-12-05T10:00:00Z', 'data': 'content'},
        ]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        with (
            pytest.raises(NotImplementedError),
            caplog.at_level(logging.ERROR),
        ):
            ingestion_task.ingest_object()
            assert f'An error occurred trying to process {TEST_OBJECT_KEY}' in caplog.text
            assert 'Please override the process_record method and tailor to your use case.' \
                in caplog.text

    def test_ingest_object_increments_skipped_counter(
        self, s3_object_processor, caplog, ingestion_task,
    ):
        object_definition = (TEST_OBJECT_KEY, compressed_json_faker([
            {'modified': '2024-12-05T10:00:00Z', 'data': 'content'},
        ]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        assert ingestion_task.skipped_counter == 0
        with (
            mock.patch.object(ingestion_task, '_should_process_record', return_value=False),
            caplog.at_level(logging.INFO),
        ):
            ingestion_task.ingest_object()
        assert ingestion_task.skipped_counter == 1

    def test_ingest_object_calls_additional_methods(
        self, s3_object_processor, caplog, ingestion_task,
    ):
        """Test that _create_ingested_object_instance and _log_ingestion_metrics are called."""
        object_definition = (TEST_OBJECT_KEY, compressed_json_faker([
            {'modified': '2024-12-05T10:00:00Z', 'data': 'content'},
        ]))
        upload_objects_to_s3(s3_object_processor, [object_definition])
        with (
            mock.patch.object(ingestion_task, '_process_record', return_value=None),
            # TODO: explore mocking the methods to assert they've been called
            # mock.patch.object(ingestion_task, '_create_ingested_object_instance') \
                # as mock_create_ingested_object,
            # mock.patch.object(ingestion_task, '_log_ingestion_metrics') as mock_log_ingestion,
            caplog.at_level(logging.INFO),
        ):
            ingestion_task.ingest_object()
            # assert mock_create_ingested_object.assert_called_once()
            # assert mock_log_ingestion.assert_called()
            assert f'IngestObject instance created for {TEST_OBJECT_KEY}' in caplog.text
            assert f'{ingestion_task.object_key} ingested.' in caplog.text

    def test_get_record_from_line(self, ingestion_task):
        deserialized_line = {'data': 'content'}
        record = ingestion_task._get_record_from_line(deserialized_line)
        assert record == deserialized_line

    def test_should_process_record_returns_true_when_no_last_ingestion_datetime(
        self, ingestion_task,
    ):
        ingestion_task.last_ingestion_datetime = None
        assert ingestion_task._should_process_record({'modified': '2024-12-04T10:00:00Z'})

    def test_should_process_record_returns_true_when_error_determining_datetime(
        self, caplog, ingestion_task,
    ):
        ingestion_task.last_ingestion_datetime = datetime(
            2024, 12, 4, 10, 0, 0, tzinfo=timezone.utc,
        )
        with caplog.at_level(logging.ERROR):
            assert ingestion_task._should_process_record({'modified': 'invalid-datetime'})
            assert 'An error occurred determining the last modified datetime' in caplog.text

    def test_should_process_record_returns_true_when_modified_gte_last_ingestion(
        self, ingestion_task,
    ):
        ingestion_task.last_ingestion_datetime = datetime(
            2024, 12, 4, 10, 0, 0, tzinfo=timezone.utc,
        )
        assert ingestion_task._should_process_record({'modified': '2024-12-05T10:00:00Z'})

    def test_should_process_record_returns_false_when_modified_lt_last_ingestion(
        self, ingestion_task,
    ):
        ingestion_task.last_ingestion_datetime = datetime(
            2024, 12, 4, 10, 0, 0, tzinfo=timezone.utc,
        )
        assert not ingestion_task._should_process_record({'modified': '2024-12-02T10:00:00Z'})

    def test_get_modified_datetime_str(self, ingestion_task):
        incoming_modified_str = '2024-12-05T10:00:00Z'
        record = {'modified': incoming_modified_str, 'data': 'content'}
        modified_datetime_str = ingestion_task._get_modified_datetime_str(record)
        assert modified_datetime_str == incoming_modified_str

    def test_process_record_raises_not_implemented_error(self, caplog, ingestion_task):
        with (
            pytest.raises(NotImplementedError),
            caplog.at_level(logging.ERROR),
        ):
            ingestion_task._process_record({'data': 'content'})
            assert 'Please override the _process_record method and tailor to your use case.' \
                in caplog.text

    def test_create_ingested_object_instance(self, caplog, ingestion_task):
        last_modified = datetime(2024, 12, 4, 10, 0, 0, tzinfo=timezone.utc)
        assert IngestedObject.objects.count() == 0
        with (
            mock.patch.object(
                S3ObjectProcessor, 'get_object_last_modified_datetime', return_value=last_modified,
            ),
            caplog.at_level(logging.INFO),
        ):
            ingestion_task._create_ingested_object_instance()
            assert f'IngestObject instance created for {TEST_OBJECT_KEY}' in caplog.text
        assert IngestedObject.objects.filter(object_key=TEST_OBJECT_KEY).exists()
        assert IngestedObject.objects.count() == 1

    def test_log_ingestion_metrics(self, ingestion_task, caplog):
        ingestion_task.created_ids = [str(uuid4())]
        ingestion_task.updated_ids = [str(uuid4()), str(uuid4())]
        ingestion_task.errors = [{str(uuid4()): 'An error occurred'}]
        ingestion_task.skipped_counter = 3
        with caplog.at_level(logging.INFO):
            ingestion_task._log_ingestion_metrics()
            assert f'{ingestion_task.object_key} ingested.' in caplog.text
            assert f'1 records created: {ingestion_task.created_ids}' in caplog.text
            assert f'2 records updated: {ingestion_task.updated_ids}' in caplog.text
            assert f'1 records failed validation: {ingestion_task.errors}' in caplog.text
            assert '3 records skipped' in caplog.text
