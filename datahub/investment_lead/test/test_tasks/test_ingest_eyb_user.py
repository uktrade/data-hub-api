import logging

from unittest import mock

import pytest
import reversion

from moto import mock_aws
from reversion.models import Version

from datahub.core.queues.constants import THREE_MINUTES_IN_SECONDS
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
from datahub.investment_lead.serializers import CreateEYBLeadUserSerializer
from datahub.investment_lead.tasks.ingest_eyb_marketing import eyb_marketing_identification_task
from datahub.investment_lead.tasks.ingest_eyb_user import (
    eyb_user_identification_task,
    eyb_user_ingestion_task,
    EYBUserIngestionTask,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_user_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def s3_object_processor(s3_client):
    """Fixture for an S3ObjectProcessor instance."""
    return S3ObjectProcessor(
        prefix=USER_PREFIX,
        region=AWS_REGION,
        bucket=S3_BUCKET_NAME,
        s3_client=s3_client,
    )


@pytest.fixture
def user_object_key():
    return f'{USER_PREFIX}object.json.gz'


@mock_aws
def test_identification_task_schedules_ingestion_task(user_object_key, caplog):
    with (
        mock.patch('datahub.ingest.tasks.job_scheduler') as mock_scheduler,
        mock.patch.object(
            S3ObjectProcessor, 'get_most_recent_object_key', return_value=user_object_key,
        ),
        mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=False),
        caplog.at_level(logging.INFO),
    ):
        eyb_user_identification_task()

        assert 'EYB user identification task started...' in caplog.text
        assert f'Scheduled ingestion of {user_object_key}' in caplog.text
        assert 'EYB user identification task finished.' in caplog.text

        mock_scheduler.assert_called_once_with(
            function=eyb_user_ingestion_task,
            function_kwargs={
                'object_key': user_object_key,
            },
            job_timeout=THREE_MINUTES_IN_SECONDS,
            queue_name='long-running',
            description=f'Ingest {user_object_key}',
        )


@mock_aws
def test_ingestion_task_triggers_company_linking(
    user_object_key, s3_object_processor, caplog,
):
    records = [eyb_lead_user_record_faker()]
    object_definition = (
        user_object_key, compressed_json_faker(records, key_to_nest_records_under='object'),
    )
    upload_objects_to_s3(s3_object_processor, [object_definition])

    with (
        mock.patch('datahub.investment_lead.tasks.ingest_eyb_user.link_leads_to_companies')
        as mocked_company_linking_task,
        caplog.at_level(logging.INFO),
    ):
        eyb_user_ingestion_task(user_object_key)

        mocked_company_linking_task.assert_called_once()
        assert 'Linked leads to companies' in caplog.text


@mock_aws
def test_ingestion_task_schedules_marketing_identification_task(
    user_object_key, s3_object_processor, caplog,
):
    records = [eyb_lead_user_record_faker()]
    object_definition = (
        user_object_key, compressed_json_faker(records, key_to_nest_records_under='object'),
    )
    upload_objects_to_s3(s3_object_processor, [object_definition])

    with (
        mock.patch('datahub.investment_lead.tasks.ingest_eyb_user.job_scheduler')
        as mock_scheduler,
        caplog.at_level(logging.INFO),
    ):
        eyb_user_ingestion_task(user_object_key)

        assert 'EYB user ingestion task started...' in caplog.text
        assert 'EYB user ingestion task finished.' in caplog.text
        assert EYBLead.objects.filter(user_hashed_uuid=records[0]['hashedUuid']).exists()

        assert 'EYB user ingestion task has scheduled EYB marketing identification task' \
            in caplog.text
        mock_scheduler.assert_called_once_with(
            function=eyb_marketing_identification_task,
            description='Identify new EYB marketing objects',
        )


@mock_aws
class TestEYBUserIngestionTask:

    @pytest.fixture
    def ingestion_task(self, user_object_key):
        return EYBUserIngestionTask(
            object_key=user_object_key,
            s3_processor=S3ObjectProcessor(prefix=USER_PREFIX),
            serializer_class=CreateEYBLeadUserSerializer,
        )

    def test_get_hashed_uuid(self, ingestion_task):
        record = eyb_lead_user_record_faker()
        assert ingestion_task._get_hashed_uuid(record) == record['hashedUuid']

    def test_get_record_from_line(self, ingestion_task):
        deserialized_line = {'object': eyb_lead_user_record_faker()}
        assert ingestion_task._get_record_from_line(deserialized_line) == \
            deserialized_line['object']

    def test_process_record_creates_eyb_lead_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = eyb_lead_user_record_faker({'hashedUuid': hashed_uuid})

        ingestion_task._process_record(record)

        assert len(ingestion_task.created_ids) == 1
        assert len(ingestion_task.updated_ids) == 0
        assert len(ingestion_task.errors) == 0
        assert EYBLead.objects.filter(user_hashed_uuid=hashed_uuid).exists()

    def test_process_record_creates_initial_revision_for_new_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = eyb_lead_user_record_faker({'hashedUuid': hashed_uuid})

        ingestion_task._process_record(record)

        instance = EYBLead.objects.get(user_hashed_uuid=hashed_uuid)
        assert Version.objects.get_for_object(instance).count() == 1

    def test_process_record_updates_eyb_lead_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        existing_lead = EYBLeadFactory(
            user_hashed_uuid=hashed_uuid,
            role='Developer',
        )
        assert EYBLead.objects.count() == 1

        new_role = 'CEO'
        record = eyb_lead_user_record_faker(
            {'hashedUuid': hashed_uuid, 'role': new_role},
        )

        ingestion_task._process_record(record)
        existing_lead.refresh_from_db()

        assert len(ingestion_task.created_ids) == 0
        assert len(ingestion_task.updated_ids) == 1
        assert len(ingestion_task.errors) == 0
        assert EYBLead.objects.count() == 1
        assert existing_lead.role == new_role

    def test_process_record_creates_new_revision_for_updated_instance(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        with reversion.create_revision():
            existing_lead = EYBLeadFactory(
                user_hashed_uuid=hashed_uuid,
                role='Developer',
            )
        assert Version.objects.get_for_object(existing_lead).count() == 1

        record = eyb_lead_user_record_faker(
            {'hashedUuid': hashed_uuid, 'role': 'CEO'},
        )
        ingestion_task._process_record(record)
        existing_lead.refresh_from_db()

        assert Version.objects.get_for_object(existing_lead).count() == 2

    def test_process_record_handles_invalid_data(self, ingestion_task):
        hashed_uuid = generate_hashed_uuid()
        record = {'hashedUuid': hashed_uuid}  # records with missing fields are invalid
        ingestion_task._process_record(record)

        assert len(ingestion_task.created_ids) == 0
        assert len(ingestion_task.updated_ids) == 0
        assert len(ingestion_task.errors) == 1
        assert ingestion_task.errors[0]['record'] == record
        assert EYBLead.objects.count() == 0
