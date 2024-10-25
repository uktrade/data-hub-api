import logging

import pytest

from moto import mock_aws

from datahub.company.models import Company, Contact
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.company_activity.models import IngestedFile
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BUCKET,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    ingest_eyb_user_data,
    USER_PREFIX,
)
from datahub.investment_lead.test.factories import (
    eyb_lead_user_record_faker
)
from datahub.investment_lead.test.test_tasks.utils import (
    file_contents_faker,
    setup_s3_bucket,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user_file_path():
    return f'{USER_PREFIX}user.jsonl.gz'


class TestEYBCompanyContactLinking:
    @mock_aws
    def test_create_company_and_contact_success(self, caplog, test_user_file_path):
        """
        Test that a EYB user data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_company_count = Company.objects.count()
        initial_contact_count = Contact.objects.count()
        initial_ingested_count = IngestedFile.objects.count()

        records = [
            # Created record
            eyb_lead_user_record_faker(),
            eyb_lead_user_record_faker(),
        ]

        file_contents = file_contents_faker(records=records)
        setup_s3_bucket(BUCKET, [test_user_file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_user_data(BUCKET, test_user_file_path)

        assert EYBLead.objects.count() == initial_eyb_lead_count + 2
        assert IngestedFile.objects.count() == initial_ingested_count + 1
        assert Company.objects.count() > initial_company_count
        assert Contact.objects.count() > initial_contact_count

    @mock_aws
    def test_linking_existing_success(self, caplog, test_user_file_path):
        """
        Test that a EYB user data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """

        company = CompanyFactory(duns_number='123')

        initial_eyb_lead_count = EYBLead.objects.count()
        initial_company_count = Company.objects.count()
        initial_contact_count = Contact.objects.count()
        initial_ingested_count = IngestedFile.objects.count()

        records = [
            # Created record
            eyb_lead_user_record_faker({'dunsNumber': '123'}),
        ]

        file_contents = file_contents_faker(records=records)
        setup_s3_bucket(BUCKET, [test_user_file_path], [file_contents])
        with caplog.at_level(logging.INFO):
            ingest_eyb_user_data(BUCKET, test_user_file_path)

        assert EYBLead.objects.count() == initial_eyb_lead_count + 1
        assert IngestedFile.objects.count() == initial_ingested_count + 1
        assert Company.objects.count() == initial_company_count
        assert Contact.objects.count() == initial_contact_count

        eyb_lead = EYBLead.objects.all()[0]
        assert eyb_lead.duns_number == '123'
        assert eyb_lead.company == company
