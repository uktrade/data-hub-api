import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.constants import InvestmentProjectStage
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

        expected_data = {
            'adviser_id': str(self.user.id),
            'annual_summaries': [
                {
                    'financial_year': {
                        'label': '2016-17',
                        'start': '2016-04-01',
                        'end': '2017-03-31',
                    },
                    'totals': {
                        'prospect': {
                            'label': 'Prospect',
                            'id': InvestmentProjectStage.prospect.value.id,
                            'value': 0,
                        },
                        'assign_pm': {
                            'label': 'Assign PM',
                            'id': InvestmentProjectStage.assign_pm.value.id,
                            'value': 0,
                        },
                        'active': {
                            'label': 'Active',
                            'id': InvestmentProjectStage.active.value.id,
                            'value': 0,
                        },
                        'verify_win': {
                            'label': 'Verify Win',
                            'id': InvestmentProjectStage.verify_win.value.id,
                            'value': 0,
                        },
                        'won': {
                            'label': 'Won',
                            'id': InvestmentProjectStage.won.value.id,
                            'value': 0,
                        },
                    },
                },
                {
                    'financial_year': {
                        'label': '2015-16',
                        'start': '2015-04-01',
                        'end': '2016-03-31',
                    },
                    'totals': {
                        'prospect': {
                            'label': 'Prospect',
                            'id': InvestmentProjectStage.prospect.value.id,
                            'value': 0,
                        },
                        'assign_pm': {
                            'label': 'Assign PM',
                            'id': InvestmentProjectStage.assign_pm.value.id,
                            'value': 0,
                        },
                        'active': {
                            'label': 'Active',
                            'id': InvestmentProjectStage.active.value.id,
                            'value': 0,
                        },
                        'verify_win': {
                            'label': 'Verify Win',
                            'id': InvestmentProjectStage.verify_win.value.id,
                            'value': 0,
                        },
                        'won': {
                            'label': 'Won',
                            'id': InvestmentProjectStage.won.value.id,
                            'value': 0,
                        },
                    },
                },
                {
                    'financial_year': {
                        'label': '2014-15',
                        'start': '2014-04-01',
                        'end': '2015-03-31',
                    },
                    'totals': {
                        'prospect': {
                            'label': 'Prospect',
                            'id': InvestmentProjectStage.prospect.value.id,
                            'value': 0,
                        },
                        'assign_pm': {
                            'label': 'Assign PM',
                            'id': InvestmentProjectStage.assign_pm.value.id,
                            'value': 0,
                        },
                        'active': {
                            'label': 'Active',
                            'id': InvestmentProjectStage.active.value.id,
                            'value': 0,
                        },
                        'verify_win': {
                            'label': 'Verify Win',
                            'id': InvestmentProjectStage.verify_win.value.id,
                            'value': 0,
                        },
                        'won': {
                            'label': 'Won',
                            'id': InvestmentProjectStage.won.value.id,
                            'value': 0,
                        },
                    },
                },
            ],
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_data
