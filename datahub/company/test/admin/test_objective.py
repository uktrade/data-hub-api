import pytest

from django.urls import reverse

from datahub.core.test_utils import AdminTestMixin

pytestmark = pytest.mark.django_db


class TestObjectiveAdmin(AdminTestMixin):
    """Tests for the CompanyExport model in the django admin site."""

    def test_objective_progress_validation_throws_error_for_more_than_allowed_max(self):
        """
        Test an error is received when the number of team members being saved is above the
        maximum allowed
        """
        url = reverse('admin:company_objective_add')

        response = self.client.post(
            url,
            {'progress': 101},
        )
        form_errors = response.context_data['adminform'].errors
        assert 'progress' in form_errors
        assert form_errors['progress'] == [
            'Ensure this value is less than or equal to 100.',
        ]
