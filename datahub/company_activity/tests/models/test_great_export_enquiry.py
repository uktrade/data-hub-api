import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tests.factories import GreatExportEnquiryFactory


@pytest.mark.django_db
class TestGreatExportEnquiry:
    """Tests for the Great Export Enquiry model."""

    def test_save(self):
        """Test save also saves to the `CompanyActivity` model and does not save to the
        `CompanyActivity` model if it already exists.
        """
        assert not CompanyActivity.objects.all().exists()
        great_export_enquiry = GreatExportEnquiryFactory()
        assert CompanyActivity.objects.all().count() == 1

        company_activity = CompanyActivity.objects.get(
            great_export_enquiry_id=great_export_enquiry.id,
        )
        assert company_activity.company_id == great_export_enquiry.company_id
        assert company_activity.date == great_export_enquiry.form_created_at
        assert (
            company_activity.activity_source == CompanyActivity.ActivitySource.great_export_enquiry
        )

        # Update and save the great export enquiry and ensure if doesn't create another
        # `CompanyActivity` and only updates it
        new_company = CompanyFactory()
        great_export_enquiry.company_id = new_company.id
        great_export_enquiry.save()

        assert CompanyActivity.objects.all().count() == 1
        company_activity.refresh_from_db()
        assert company_activity.company_id == new_company.id

        great_export_enquiry.delete()
        assert not CompanyActivity.objects.all().exists()

    def test_save_with_no_company(self):
        """Test save does not save to the `CompanyActivity` model.
        """
        assert not CompanyActivity.objects.all().exists()

        # Try to save the great export enquiry with no company id which will not work
        GreatExportEnquiryFactory(company_id=None)

        assert not CompanyActivity.objects.all().exists()
