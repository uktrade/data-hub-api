import pytest

from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tests.factories import CompanyActivityGreatExportEnquiryFactory


@pytest.mark.django_db
class TestCompanyActivityGreatExportEnquiryFactory:

    def test_factory_does_not_create_duplicates(self):
        """
        As the GreatExportEnquiry models save method is overwritten to create a company
        activity. The _create method on the factory returns the created activity from the save
        rather than creating a new one causing duplicates.
        """
        CompanyActivityGreatExportEnquiryFactory()
        assert CompanyActivity.objects.count() == 1
