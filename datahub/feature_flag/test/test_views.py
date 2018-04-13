import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.feature_flag.test.factories import FeatureFlagFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestListFeatureFlags(APITestMixin):
    """Tests for listing of feature flags."""

    def test_can_list_feature_flags_having_no_permissions(self, api_client):
        """Should return 401"""
        url = reverse('api-v3:feature-flag:collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_can_list_feature_flags(self):
        """List feature flags.."""
        feature_flags = FeatureFlagFactory.create_batch(
            2,
            code=factory.Iterator(('def', 'abc',))
        )
        url = reverse('api-v3:feature-flag:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'code': feature_flags[1].code,
                    'description': feature_flags[1].description,
                    'is_active': feature_flags[1].is_active,
                }, {
                    'code': feature_flags[0].code,
                    'description': feature_flags[0].description,
                    'is_active': feature_flags[0].is_active,
                }
            ]
        }
