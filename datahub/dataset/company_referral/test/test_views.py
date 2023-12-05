from datetime import datetime

import pytest

from django.urls import reverse

from django.utils.timezone import utc

from freezegun import freeze_time

from rest_framework import status

from datahub.company_referral.test.factories import (
    ClosedCompanyReferralFactory,
    CompanyReferralFactory,
)
from datahub.core.test_utils import format_date_or_datetime, get_attr_or_none
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_company_referral(referral):
    """Returns company referral data as a dictionary"""
    return {
        'company_id': str(referral.company_id),
        'completed_by_id': get_attr_or_none(referral, 'completed_by_id'),
        'completed_on': format_date_or_datetime(referral.completed_on),
        'contact_id': str(referral.contact_id),
        'created_by_id': str(referral.created_by_id),
        'created_on': format_date_or_datetime(referral.created_on),
        'id': str(referral.id),
        'interaction_id': (
            str(referral.interaction_id)
            if referral.interaction_id is not None
            else None
        ),
        'notes': referral.notes,
        'recipient_id': str(referral.recipient_id),
        'status': str(referral.status),
        'subject': referral.subject,
    }


@pytest.mark.django_db
class TestCompanyReferralDatasetView(BaseDatasetViewTest):
    """
    Tests for CompanyReferralDatasetView
    """

    view_url = reverse('api-v4:dataset:company-referrals-dataset')
    factory = CompanyReferralFactory

    @pytest.mark.parametrize(
        'referral_factory', (
            CompanyReferralFactory,
            ClosedCompanyReferralFactory,
        ),
    )
    def test_success(self, data_flow_api_client, referral_factory):
        """Test that endpoint returns with expected data for a single referral"""
        referral = referral_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_company_referral(referral)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        with freeze_time('2019-01-01 12:30:00'):
            referral1 = CompanyReferralFactory()
        with freeze_time('2019-01-03 12:00:00'):
            referral2 = CompanyReferralFactory()
        with freeze_time('2019-01-01 12:00:00'):
            referral3 = CompanyReferralFactory()
            referral4 = CompanyReferralFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted([referral3, referral4], key=lambda x: x.pk) + [referral1, referral2]
        for index, referral in enumerate(expected_list):
            assert str(referral.id) == response_results[index]['id']

    def test_with_updated_since_filter(self, data_flow_api_client):
        with freeze_time('2021-01-01 12:30:00'):
            self.factory()
        with freeze_time('2022-01-01 12:30:00'):
            company_export_after = self.factory()
        # Define the `updated_since` date
        updated_since_date = datetime(2021, 2, 1, tzinfo=utc).strftime('%Y-%m-%d')

        # Make the request with the `updated_since` parameter
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})

        assert response.status_code == status.HTTP_200_OK

        # Check that only companies created after the `updated_since` date are returned
        expected_ids = [str(company_export_after.id)]
        response_ids = [company['id'] for company in response.json()['results']]

        assert response_ids == expected_ids
