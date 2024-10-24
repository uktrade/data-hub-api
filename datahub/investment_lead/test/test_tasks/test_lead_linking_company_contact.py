import logging

import pytest

from moto import mock_aws

from datahub.company_activity.models import IngestedFile
from datahub.investment_lead.models import EYBLead
from datahub.company.models import Company, Contact
from datahub.investment_lead.tasks.ingest_eyb_common import (
    BUCKET,
)
from datahub.investment_lead.tasks.ingest_eyb_user import (
    ingest_eyb_user_data,
)
from datahub.investment_lead.test.test_tasks.utils import (
    file_contents_faker,
    setup_s3_bucket,
)


pytestmark = pytest.mark.django_db


class TestEYBCompanyContactLinking:
    @mock_aws
    def test_linking_success(self, caplog, test_user_file_path):
        """
        Test that a EYB user data file is ingested correctly and the ingested
        file is added to the IngestedFile table
        """
        initial_eyb_lead_count = EYBLead.objects.count()
        initial_company_count = Company.objects.count()
        initial_contact_count = Contact.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        file_contents = file_contents_faker(default_faker='user')
        setup_s3_bucket(BUCKET, [test_user_file_path], [file_contents])
        
        with caplog.at_level(logging.INFO):
            ingest_eyb_user_data(BUCKET, test_user_file_path)

        assert EYBLead.objects.count() > initial_eyb_lead_count
        assert IngestedFile.objects.count() == initial_ingested_count + 1
        assert Company.objects.count() > initial_company_count
        assert Contact.objects.count() > initial_contact_count
