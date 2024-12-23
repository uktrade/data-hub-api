import pytest

from moto import mock_aws

from datahub.company.models import Company, Contact
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BUCKET,
)
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    ingest_eyb_triage_data,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    ingest_eyb_user_data,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_triage_record_faker,
    eyb_lead_user_record_faker,
    generate_hashed_uuid,
)
from datahub.investment_lead.test.test_tasks.utils import (
    file_contents_faker,
    setup_s3_bucket,
)
from datahub.investment_lead.test.utils import (
    assert_eyb_lead_matches_company,
    assert_eyb_lead_matches_contact,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_triage_file_path():
    return f'{TRIAGE_PREFIX}/triage.jsonl.gz'


@pytest.fixture
def test_user_file_path():
    return f'{USER_PREFIX}user.jsonl.gz'


class TestEYBCompanyContactLinking:
    @mock_aws
    def test_create_company_and_contact_success(
        self, test_triage_file_path, test_user_file_path,
    ):
        """
        Test ingests triage and user data without any pre existing company and contacts
        and verifies that their creation + linking to the EYB lead happens correctly
        """
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
            }),
        ]

        triage_file_contents = file_contents_faker(records=triage_records)
        user_file_contents = file_contents_faker(records=user_records)

        setup_s3_bucket(
            BUCKET,
            [test_triage_file_path, test_user_file_path],
            [triage_file_contents, user_file_contents],
        )

        ingest_eyb_triage_data(BUCKET, test_triage_file_path)
        ingest_eyb_user_data(BUCKET, test_user_file_path)

        assert EYBLead.objects.count() == initial_eyb_lead_count + 1
        assert Company.objects.count() == initial_company_count + 1
        assert Contact.objects.count() == initial_contact_count + 1

        eyb_lead = EYBLead.objects.all()[0]
        company = Company.objects.all()[0]
        assert_eyb_lead_matches_company(company, eyb_lead)

        assert eyb_lead.company.contacts.count() == 1
        contact = eyb_lead.company.contacts.first()
        assert_eyb_lead_matches_contact(contact, eyb_lead)

    @mock_aws
    def test_linking_existing_company_contact_success(
        self, test_triage_file_path, test_user_file_path,
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

        triage_file_contents = file_contents_faker(records=triage_records)
        user_file_contents = file_contents_faker(records=user_records)

        setup_s3_bucket(
            BUCKET,
            [test_triage_file_path, test_user_file_path],
            [triage_file_contents, user_file_contents],
        )

        ingest_eyb_triage_data(BUCKET, test_triage_file_path)
        ingest_eyb_user_data(BUCKET, test_user_file_path)

        assert EYBLead.objects.count() == initial_eyb_lead_count + 1
        assert Company.objects.count() == initial_company_count
        assert Contact.objects.count() == initial_contact_count

        eyb_lead = EYBLead.objects.all()[0]
        company = Company.objects.all()[0]
        assert eyb_lead.company == company

        assert eyb_lead.company.contacts.count() == 1
        from_company_contact = eyb_lead.company.contacts.first()
        assert contact == from_company_contact
