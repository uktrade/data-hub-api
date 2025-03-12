import logging

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from unittest import mock

import pytest

from django.core.management import call_command
from freezegun import freeze_time

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.constants import (
    AWS_REGION,
    S3_BUCKET_NAME,
    TEST_PREFIX,
)
from datahub.ingest.models import IngestedObject
from datahub.ingest.test.factories import IngestedObjectFactory
from datahub.ingest.utils import (
    compressed_json_faker,
    upload_objects_to_s3,
)
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_eyb_marketing import MARKETING_PREFIX
from datahub.investment_lead.tasks.ingest_eyb_triage import TRIAGE_PREFIX
from datahub.investment_lead.tasks.ingest_eyb_user import USER_PREFIX
from datahub.investment_lead.test.factories import (
    eyb_lead_marketing_record_faker,
    eyb_lead_triage_record_faker,
    eyb_lead_user_record_faker,
    EYBLeadFactory,
    generate_hashed_uuid,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def s3_object_processor(s3_client):
    """Fixture for an S3ObjectProcessor instance."""
    return S3ObjectProcessor(
        prefix=TEST_PREFIX,
        region=AWS_REGION,
        bucket=S3_BUCKET_NAME,
        s3_client=s3_client,
    )


def test_schedule_reingestion_of_eyb_leads(s3_object_processor, caplog):
    # Define objects to ingest from
    new_hashed_uuid = generate_hashed_uuid()
    existing_hashed_uuid = generate_hashed_uuid()

    # Triage
    triage_records = [
        eyb_lead_triage_record_faker({'hashedUuid': new_hashed_uuid}),
        eyb_lead_triage_record_faker({'hashedUuid': existing_hashed_uuid}),
    ]
    triage_object_definition = (
        f'{TRIAGE_PREFIX}object.json.gz',
        compressed_json_faker(triage_records, key_to_nest_records_under='object'),
    )

    # User
    user_records = [
        eyb_lead_user_record_faker({'hashedUuid': new_hashed_uuid}),
        eyb_lead_user_record_faker({'hashedUuid': existing_hashed_uuid}),
    ]
    user_object_definition = (
        f'{USER_PREFIX}object.json.gz',
        compressed_json_faker(user_records, key_to_nest_records_under='object'),
    )

    # Marketing
    marketing_records = [
        eyb_lead_marketing_record_faker({'hashed_uuid': new_hashed_uuid}),
        eyb_lead_marketing_record_faker({'hashed_uuid': existing_hashed_uuid}),
    ]
    marketing_object_definition = (
        f'{MARKETING_PREFIX}object.json.gz',
        compressed_json_faker(marketing_records),
    )

    yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
    with freeze_time(yesterday):
        upload_objects_to_s3(s3_object_processor, [
            triage_object_definition,
            user_object_definition,
            marketing_object_definition,
        ])

        EYBLeadFactory(
            triage_hashed_uuid=existing_hashed_uuid,
            user_hashed_uuid=existing_hashed_uuid,
            marketing_hashed_uuid=existing_hashed_uuid,
        )
        IngestedObjectFactory(object_key=triage_object_definition[0])
        IngestedObjectFactory(object_key=user_object_definition[0])
        IngestedObjectFactory(object_key=marketing_object_definition[0])
        unrelated_ingested_object = IngestedObjectFactory(object_key='unrelated/object/key.json')

    # Initial assertions
    assert EYBLead.objects.count() == 1
    assert IngestedObject.objects.count() == 4

    # Execute job
    with caplog.at_level(logging.INFO):
        call_command('schedule_reingestion_of_eyb_leads')
        assert 'Deleted 3 EYB IngestedObject instances' in caplog.text
        assert 'Scheduled re-ingestion of latest EYB objects' in caplog.text

    # Final assertions
    assert EYBLead.objects.count() == 2
    for eyb_lead in EYBLead.objects.all():
        assert eyb_lead.modified_on > yesterday

    assert IngestedObject.objects.count() == 4
    assert IngestedObject.objects.filter(pk=unrelated_ingested_object.pk).exists()
    unrelated_ingested_object.refresh_from_db()
    assert unrelated_ingested_object.created == yesterday
    for ingested_object in IngestedObject.objects.exclude(pk=unrelated_ingested_object.pk):
        assert ingested_object.created > yesterday


def test_schedule_reingestion_of_eyb_leads_handles_error(caplog):
    with (
        mock.patch('datahub.ingest.models.IngestedObject.objects')
        as mock_objects,
        caplog.at_level(logging.ERROR),
    ):
        mock_objects.filter.side_effect = Exception('A mocked filtering error')
        call_command('schedule_reingestion_of_eyb_leads')
        assert (
            'An error occurred trying to schedule the re-ingestion of all records '
            'from latest EYB objects:'
        ) in caplog.text
