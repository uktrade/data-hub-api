import pytest

from moto import mock_aws

from datahub.company.models import Company, Contact
from datahub.company.test.factories import CompanyFactory, ContactFactory
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
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    eyb_triage_ingestion_task,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    eyb_user_ingestion_task,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_triage_record_faker,
    eyb_lead_user_record_faker,
    generate_hashed_uuid,
)
from datahub.investment_lead.test.utils import (
    assert_eyb_lead_matches_company,
    assert_eyb_lead_matches_contact,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def triage_object_key():
    return f'{TRIAGE_PREFIX}triage.jsonl.gz'


@pytest.fixture
def triage_object_processor(s3_client):
    """Fixture for an S3ObjectProcessor instance pointed at the triage prefix."""
    return S3ObjectProcessor(
        prefix=TRIAGE_PREFIX,
        region=AWS_REGION,
        bucket=S3_BUCKET_NAME,
        s3_client=s3_client,
    )


@pytest.fixture
def user_object_key():
    return f'{USER_PREFIX}user.jsonl.gz'


@pytest.fixture
def user_object_processor(s3_client):
    """Fixture for an S3ObjectProcessor instance pointed at the user prefix."""
    return S3ObjectProcessor(
        prefix=USER_PREFIX,
        region=AWS_REGION,
        bucket=S3_BUCKET_NAME,
        s3_client=s3_client,
    )


@mock_aws
class TestEYBCompanyContactLinking:

    def test_create_company_and_contact_success(
        self,
        triage_object_key,
        user_object_key,
        triage_object_processor,
        user_object_processor,
    ):
        """
        Test ingests triage and user data without any pre existing company and contacts
        and verifies that their creation + linking to the EYB lead happens correctly
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_company_count = Company.objects.count()
        initial_contact_count = Contact.objects.count()
        hashed_uuid = generate_hashed_uuid()

        triage_records = [eyb_lead_triage_record_faker({'hashedUuid': hashed_uuid})]
        user_records = [eyb_lead_user_record_faker({'hashedUuid': hashed_uuid})]

        for object_key, records, object_processor in [
            (triage_object_key, triage_records, triage_object_processor),
            (user_object_key, user_records, user_object_processor),
        ]:
            object_definition = (
                object_key, compressed_json_faker(records, key_to_nest_records_under='object'),
            )
            upload_objects_to_s3(object_processor, [object_definition])

        eyb_triage_ingestion_task(triage_object_key)
        eyb_user_ingestion_task(user_object_key)

        assert EYBLead.objects.count() == initial_eyb_lead_count + 1
        assert Company.objects.count() == initial_company_count + 1
        assert Contact.objects.count() == initial_contact_count + 1

        eyb_lead = EYBLead.objects.all()[0]
        company = Company.objects.all()[0]
        assert_eyb_lead_matches_company(company, eyb_lead)

        assert eyb_lead.company.contacts.count() == 1
        contact = eyb_lead.company.contacts.first()
        assert_eyb_lead_matches_contact(contact, eyb_lead)

    def test_linking_existing_company_contact_success(
        self,
        triage_object_key,
        user_object_key,
        triage_object_processor,
        user_object_processor,
    ):
        """
        Test ingests triage and user data with pre existing company and contacts
        and verifies that their match + linking to the EYB lead happens correctly
        """
        company = CompanyFactory(duns_number='123')
        contact = ContactFactory(
            company=company,
            email='foo@bar.com',
        )

        initial_eyb_lead_count = EYBLead.objects.count()
        initial_company_count = Company.objects.count()
        initial_contact_count = Contact.objects.count()
        hashed_uuid = generate_hashed_uuid()

        triage_records = [
            eyb_lead_triage_record_faker({
                'hashedUuid': hashed_uuid,
            }),
        ]

        user_records = [
            eyb_lead_user_record_faker({
                'hashedUuid': hashed_uuid,
                'dunsNumber': '123',
                'companyName': company.name,
                'email': 'foo@bar.com',
            }),
        ]

        for object_key, records, object_processor in [
            (triage_object_key, triage_records, triage_object_processor),
            (user_object_key, user_records, user_object_processor),
        ]:
            object_definition = (
                object_key, compressed_json_faker(records, key_to_nest_records_under='object'),
            )
            upload_objects_to_s3(object_processor, [object_definition])

        eyb_triage_ingestion_task(triage_object_key)
        eyb_user_ingestion_task(user_object_key)

        assert EYBLead.objects.count() == initial_eyb_lead_count + 1
        assert Company.objects.count() == initial_company_count
        assert Contact.objects.count() == initial_contact_count

        eyb_lead = EYBLead.objects.all()[0]
        company = Company.objects.all()[0]
        assert eyb_lead.company == company

        assert eyb_lead.company.contacts.count() == 1
        from_company_contact = eyb_lead.company.contacts.first()
        assert contact == from_company_contact
