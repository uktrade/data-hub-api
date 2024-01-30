import uuid

import pytest

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse


from datahub.core.constants import (
    Experience as ExperienceConstant,
    MarketingSource as MarketingSourceConstant,
    Rating as RatingConstant,
    WithoutOurSupport as WithoutOurSupportConstant,
)
from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
)
from datahub.export_win.test.factories import (
    CustomerResponseTokenFactory,
)

pytestmark = pytest.mark.django_db


class TestGetCustomerResponseView(APITestMixin):
    """Get single customer response view tests."""

    def test_win_details_no_permissions(self):
        """Should return 404"""
        CustomerResponseTokenFactory()
        api_client = self.create_api_client(user=None)
        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get(self):
        """Test getting a single customer repsonse."""
        token = CustomerResponseTokenFactory()
        api_client = self.create_api_client(user=None)
        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})
        response = api_client.get(url)
        customer_response = token.customer_response
        win = customer_response.win

        expected_response = {
            'win': {
                'date': format_date_or_datetime(win.date),
                'country': {
                    'id': str(win.country.id),
                    'name': win.country.name,
                },
                'goods_vs_services': {
                    'id': str(win.goods_vs_services.id),
                    'name': win.goods_vs_services.name,
                },
                'lead_officer': {
                    'id': str(win.lead_officer.id),
                    'name': win.lead_officer.name,
                    'first_name': win.lead_officer.first_name,
                    'last_name': win.lead_officer.last_name,
                },
                'description': win.description,
                'breakdowns': [],
            },
            'agree_with_win': customer_response.agree_with_win,
            'comments': customer_response.comments,
            'our_support': {
                'id': str(customer_response.our_support.id),
                'name': customer_response.our_support.name,
            },
            'access_to_contacts': {
                'id': str(customer_response.access_to_contacts.id),
                'name': customer_response.access_to_contacts.name,
            },
            'access_to_information': {
                'id': str(customer_response.access_to_information.id),
                'name': customer_response.access_to_information.name,
            },
            'improved_profile': {
                'id': str(customer_response.improved_profile.id),
                'name': customer_response.improved_profile.name,
            },
            'gained_confidence': {
                'id': str(customer_response.gained_confidence.id),
                'name': customer_response.gained_confidence.name,
            },
            'developed_relationships': {
                'id': str(customer_response.developed_relationships.id),
                'name': customer_response.developed_relationships.name,
            },
            'overcame_problem': {
                'id': str(customer_response.overcame_problem.id),
                'name': customer_response.overcame_problem.name,
            },
            'involved_state_enterprise': customer_response.involved_state_enterprise,
            'interventions_were_prerequisite': customer_response.interventions_were_prerequisite,
            'support_improved_speed': customer_response.support_improved_speed,
            'expected_portion_without_help': {
                'id': str(customer_response.expected_portion_without_help.id),
                'name': customer_response.expected_portion_without_help.name,
            },
            'last_export': {
                'id': str(customer_response.last_export.id),
                'name': customer_response.last_export.name,
            },
            'company_was_at_risk_of_not_exporting': False,
            'has_explicit_export_plans': False,
            'has_enabled_expansion_into_new_market': False,
            'has_increased_exports_as_percent_of_turnover': False,
            'has_enabled_expansion_into_existing_market': False,
            'case_study_willing': False,
            'marketing_source': {
                'id': str(customer_response.marketing_source.id),
                'name': customer_response.marketing_source.name,
            },
            'other_marketing_source': customer_response.other_marketing_source,
        }
        assert response.json() == expected_response

        token.refresh_from_db()
        assert token.times_used == 1

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        token.refresh_from_db()
        assert token.times_used == 2

    def test_cant_get_customer_response_with_expired_token(self):
        token = CustomerResponseTokenFactory()
        assert token.times_used == 0
        api_client = self.create_api_client(user=None)

        almost_expired = token.expires_on - relativedelta(minutes=1)

        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})
        with freeze_time(almost_expired):
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
        token.refresh_from_db()
        assert token.times_used == 1
        with freeze_time(token.expires_on):
            response = api_client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateCustomerResponseView(APITestMixin):
    """Update single customer response view tests."""

    def test_update_customer_response(self):
        """Tests successfully updating customer response."""
        token = CustomerResponseTokenFactory()
        assert token.times_used == 0
        api_client = self.create_api_client(user=None)

        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})

        experience = ExperienceConstant.we_last_exported.value
        rating_na = RatingConstant.n_a.value
        rating_5 = RatingConstant.rating_5.value
        marketing_source = MarketingSourceConstant.other.value
        without_our_support = WithoutOurSupportConstant.no_value.value
        request_data = {
            'agree_with_win': True,
            'comments': 'Comment',
            'our_support': {
                'id': rating_5.id,
            },
            'access_to_contacts': {
                'id': rating_na.id,
            },
            'access_to_information': {
                'id': rating_5.id,
            },
            'improved_profile': {
                'id': rating_5.id,
            },
            'gained_confidence': {
                'id': rating_5.id,
            },
            'developed_relationships': {
                'id': rating_na.id,
            },
            'overcame_problem': {
                'id': rating_5.id,
            },
            'involved_state_enterprise': False,
            'interventions_were_prerequisite': False,
            'support_improved_speed': True,
            'expected_portion_without_help': {
                'id': without_our_support.id,
            },
            'last_export': {
                'id': experience.id,
            },
            'company_was_at_risk_of_not_exporting': True,
            'has_explicit_export_plans': False,
            'has_enabled_expansion_into_new_market': False,
            'has_increased_exports_as_percent_of_turnover': False,
            'has_enabled_expansion_into_existing_market': False,
            'case_study_willing': False,
            'marketing_source': {
                'id': marketing_source.id,
            },
            'other_marketing_source': 'Friend',
        }
        response = api_client.patch(url, data=request_data)
        assert response.status_code == status.HTTP_200_OK

        customer_response = token.customer_response
        customer_response.refresh_from_db()
        win = customer_response.win

        expected_response = {
            'win': {
                'date': format_date_or_datetime(win.date),
                'country': {
                    'id': str(win.country.id),
                    'name': win.country.name,
                },
                'goods_vs_services': {
                    'id': str(win.goods_vs_services.id),
                    'name': win.goods_vs_services.name,
                },
                'lead_officer': {
                    'id': str(win.lead_officer.id),
                    'name': win.lead_officer.name,
                    'first_name': win.lead_officer.first_name,
                    'last_name': win.lead_officer.last_name,
                },
                'description': win.description,
                'breakdowns': [],
            },
            'agree_with_win': customer_response.agree_with_win,
            'comments': customer_response.comments,
            'our_support': {
                'id': rating_5.id,
                'name': rating_5.name,
            },
            'access_to_contacts': {
                'id': rating_na.id,
                'name': rating_na.name,
            },
            'access_to_information': {
                'id': rating_5.id,
                'name': rating_5.name,
            },
            'improved_profile': {
                'id': rating_5.id,
                'name': rating_5.name,
            },
            'gained_confidence': {
                'id': rating_5.id,
                'name': rating_5.name,
            },
            'developed_relationships': {
                'id': rating_na.id,
                'name': rating_na.name,
            },
            'overcame_problem': {
                'id': rating_5.id,
                'name': rating_5.name,
            },
            'involved_state_enterprise': False,
            'interventions_were_prerequisite': False,
            'support_improved_speed': True,
            'expected_portion_without_help': {
                'id': without_our_support.id,
                'name': without_our_support.name,
            },
            'last_export': {
                'id': experience.id,
                'name': experience.name,
            },
            'company_was_at_risk_of_not_exporting': True,
            'has_explicit_export_plans': False,
            'has_enabled_expansion_into_new_market': False,
            'has_increased_exports_as_percent_of_turnover': False,
            'has_enabled_expansion_into_existing_market': False,
            'case_study_willing': False,
            'marketing_source': {
                'id': marketing_source.id,
                'name': marketing_source.name,
            },
            'other_marketing_source': 'Friend',
        }
        assert response.json() == expected_response

        token.refresh_from_db()
        assert token.times_used == 1

        # check the token has expired after the update
        response = api_client.patch(url, data=request_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cant_update_customer_response_with_expired_token(self):
        token = CustomerResponseTokenFactory()
        api_client = self.create_api_client(user=None)

        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})

        request_data = {
            'agree_with_win': True,
        }
        with freeze_time(token.expires_on):
            response = api_client.patch(url, data=request_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDisallowedCustomerResponseViews(APITestMixin):
    """Ensure we cannot use disallowed HTTP verbs."""

    def test_list(self):
        """Test getting a list of customer repsonses."""
        api_client = self.create_api_client(user=None)
        response = api_client.get('v4/export-win/review')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put(self):
        """Test putting a single customer repsonse."""
        token = CustomerResponseTokenFactory()
        api_client = self.create_api_client(user=None)
        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})
        response = api_client.put(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post(self):
        """Test creating a single customer repsonse."""
        token = CustomerResponseTokenFactory()
        api_client = self.create_api_client(user=None)
        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})
        response = api_client.put(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete(self):
        """Test deleting a single customer repsonse."""
        token = CustomerResponseTokenFactory()
        api_client = self.create_api_client(user=None)
        url = reverse('api-v4:export-win:customer-response', kwargs={'token_pk': token.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        token.refresh_from_db()
        assert token.customer_response is not None
