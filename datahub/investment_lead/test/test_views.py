import pytest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.investment_lead.models import EYBLead
from datahub.metadata.test.factories import TeamFactory


class TestEYBLeadCreateAPI(APITestMixin):
    """
        EYB Lead Create view test case.
    """

    def test_post_not_authorized(self):
        """
            Should return 403
        """

        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        post_url = reverse('api-v4:investment-lead:create')
        response = api_client.post(post_url, data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_with_no_payload(self):
        """
            Test that we get an Exception when no payload is sent
        """

        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.post(post_url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_with_incomplete_payload(self, eyb_lead_data):
        """
            Test that we get an Exception when incomplete payload is sent
        """

        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.post(
            post_url, data={**eyb_lead_data},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_success(self, eyb_lead_data):
        """
            Test successful POST to EYB
        """

        assert EYBLead.objects.count() == 0

        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.post(
            post_url, data={**eyb_lead_data},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert EYBLead.objects.count() == 1
