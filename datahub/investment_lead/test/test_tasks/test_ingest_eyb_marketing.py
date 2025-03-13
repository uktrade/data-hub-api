import logging

from unittest import mock

import pytest

from moto import mock_aws
from reversion.models import Version

from datahub.core.queues.constants import THIRTY_MINUTES_IN_SECONDS
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import (
    AWS_REGION,
    S3_BUCKET_NAME,
)
from datahub.ingest.utils import (
    compressed_json_faker,
    upload_objects_to_s3,
)
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import CreateEYBLeadMarketingSerializer
from datahub.investment_lead.tasks.ingest_eyb_marketing import (
    eyb_marketing_identification_task,
    eyb_marketing_ingestion_task,
    EYBMarketingIngestionTask,
    MARKETING_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_marketing_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def s3_object_processor(s3_client):
    """Fixture for an S3ObjectProcessor instance."""
    return S3ObjectProcessor(
        prefix=MARKETING_PREFIX,
        region=AWS_REGION,
        bucket=S3_BUCKET_NAME,
        s3_client=s3_client,
    )


@pytest.fixture
def marketing_object_key():
    return f'{MARKETING_PREFIX}object.json.gz'


@mock_aws
def test_identification_task_schedules_ingestion_task(marketing_object_key, caplog):
    with (
        mock.patch('datahub.ingest.tasks.job_scheduler') as mock_scheduler,
        mock.patch.object(
            S3ObjectProcessor, 'get_most_recent_object_key', return_value=marketing_object_key,
        ),
        mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=False),
        caplog.at_level(logging.INFO),
    ):
        eyb_marketing_identification_task()

        assert 'EYB marketing identification task started...' in caplog.text
        assert f'Scheduled ingestion of {marketing_object_key}' in caplog.text
        assert 'EYB marketing identification task finished.' in caplog.text

        mock_scheduler.assert_called_once_with(
            function=eyb_marketing_ingestion_task,
            function_kwargs={
                'object_key': marketing_object_key,
            },
            job_timeout=THIRTY_MINUTES_IN_SECONDS,
            queue_name='long-running',
            description=f'Ingest {marketing_object_key}',
        )


@mock_aws
def test_ingestion_task_success(
    marketing_object_key, s3_object_processor, caplog,
):
    records = [eyb_lead_marketing_record_faker()]
    object_definition = (marketing_object_key, compressed_json_faker(records))
    upload_objects_to_s3(s3_object_processor, [object_definition])

    with caplog.at_level(logging.INFO):
        eyb_marketing_ingestion_task(marketing_object_key)

        assert 'EYB marketing ingestion task started...' in caplog.text
        assert 'EYB marketing ingestion task finished.' in caplog.text
        assert EYBLead.objects.filter(marketing_hashed_uuid=records[0]['hashed_uuid']).exists()


@mock_aws
def test_ingestion_task_does_not_update_existing(
    marketing_object_key, s3_object_processor, caplog,
):
    hashed_uuid = generate_hashed_uuid()
    source = 'Web'
    existing_instance = EYBLeadFactory(
        marketing_hashed_uuid=hashed_uuid,
        utm_source=source,
    )
    assert EYBLead.objects.count() == 1

    records = [
        eyb_lead_marketing_record_faker({
            'hashed_uuid': hashed_uuid,
            'utm_source': 'Advert',
        }),
    ]
    object_definition = (marketing_object_key, compressed_json_faker(records))
    upload_objects_to_s3(s3_object_processor, [object_definition])

    eyb_marketing_ingestion_task(marketing_object_key)

    assert EYBLead.objects.count() == 1
    existing_instance.refresh_from_db()
    assert existing_instance.utm_source == source


@mock_aws
class TestEYBMarketingIngestionTask:

    @pytest.fixture
    def ingestion_task(self, marketing_object_key):
        return EYBMarketingIngestionTask(
            object_key=marketing_object_key,
            s3_processor=S3ObjectProcessor(prefix=MARKETING_PREFIX),
            serializer_class=CreateEYBLeadMarketingSerializer,
        )

    def test_get_hashed_uuid(self, ingestion_task):
        record = eyb_lead_marketing_record_faker()
        assert ingestion_task._get_hashed_uuid(record) == record['hashed_uuid']

    def test_get_record_from_line(self, ingestion_task):
        deserialized_line = eyb_lead_marketing_record_faker()
        assert ingestion_task._get_record_from_line(deserialized_line) == \
            deserialized_line

    def test_should_process_record_returns_true_when_new(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = eyb_lead_marketing_record_faker({'hashed_uuid': hashed_uuid})
        assert ingestion_task._should_process_record(record) is True

    def test_should_process_record_returns_false_when_existing(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        EYBLeadFactory(marketing_hashed_uuid=hashed_uuid)
        record = eyb_lead_marketing_record_faker({'hashed_uuid': hashed_uuid})
        assert ingestion_task._should_process_record(record) is False

    def test_process_record_creates_eyb_lead_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = eyb_lead_marketing_record_faker({'hashed_uuid': hashed_uuid})

        ingestion_task._process_record(record)

        assert len(ingestion_task.created_ids) == 1
        assert len(ingestion_task.updated_ids) == 0
        assert len(ingestion_task.errors) == 0
        assert EYBLead.objects.filter(marketing_hashed_uuid=hashed_uuid).exists()

    def test_process_record_creates_initial_revision_for_new_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = eyb_lead_marketing_record_faker({'hashed_uuid': hashed_uuid})

        ingestion_task._process_record(record)

        instance = EYBLead.objects.get(marketing_hashed_uuid=hashed_uuid)
        assert Version.objects.get_for_object(instance).count() == 1

    def test_process_record_handles_invalid_data(self, ingestion_task):
        record = {}  # records with missing hashed_uuid are invalid
        ingestion_task._process_record(record)

        assert len(ingestion_task.created_ids) == 0
        assert len(ingestion_task.updated_ids) == 0
        assert len(ingestion_task.errors) == 1
        assert ingestion_task.errors[0]['record'] == record
        assert EYBLead.objects.count() == 0
