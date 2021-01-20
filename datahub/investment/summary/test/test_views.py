import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory


@pytest.mark.django_db()
class TestIProjectSummaryView(APITestMixin):
    """
    Tests for the investment project summary view.

    These cover GET /v4/adviser/<uuid:adviser_pk>/investment-summary
    """

    def test_investments_no_permissions(self):
        """User must have access."""
        user = create_test_user(dit_team=TeamFactory())
        url = reverse(
            'api-v4:investment-summary:investment-summary-item',
            kwargs={'adviser_pk': str(user.id)},
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @freeze_time('2015-04-01 12:30:00')
    def test_get_investment_summary_success(self):
        """A succesful request should return the summaries."""
        url = reverse(
            'api-v4:investment-summary:investment-summary-item',
            kwargs={'adviser_pk': str(self.user.id)},
        )
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'adviser_id': str(self.user.id),
            'annual_summaries': [
                {
                    'financial_year': '2014-15',
                    'totals': {
                        'prospect': 0,
                        'assign_pm': 0,
                        'active': 0,
                        'verify_win': 0,
                        'won': 0,
                    },
                },
                {
                    'financial_year': '2015-16',
                    'totals': {
                        'prospect': 0,
                        'assign_pm': 0,
                        'active': 0,
                        'verify_win': 0,
                        'won': 0,
                    },
                },
            ],
        }
