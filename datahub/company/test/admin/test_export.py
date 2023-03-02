import pytest

from django.urls import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import AdminTestMixin

pytestmark = pytest.mark.django_db


class TestCompanyExportAdmin(AdminTestMixin):
    """Tests for the CompanyExport model in the django admin site."""

    def test_export_team_members_validation_throws_error_for_more_than_allowed_max(self):
        """
        Test an error is received when the number of team members being saved is above the
        maximum allowed
        """
        url = reverse('admin:company_companyexport_add')

        response = self.client.post(
            url,
            {'team_members': [advisor.id for advisor in AdviserFactory.create_batch(6)]},
        )
        form_errors = response.context_data['adminform'].errors
        assert 'team_members' in form_errors
        assert form_errors['team_members'] == [
            'You can only add 5 team members',
        ]
