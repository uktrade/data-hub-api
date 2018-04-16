import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.feature_flag.test.factories import FeatureFlagFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestListFeatureFlags(APITestMixin):
    """Tests for listing of feature flags."""

    def test_cannot_list_feature_flags_having_no_permissions(self, api_client):
        """Should return 401."""
        url = reverse('api-v3:feature-flag:collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_can_get_feature_flags(self):
        """Get feature flags."""
        feature_flags = FeatureFlagFactory.create_batch(10)
        url = reverse('api-v3:feature-flag:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        expected_feature_flags = {
            feature_flag.code: feature_flag.is_active
            for feature_flag in feature_flags
        }
        assert response_data == expected_feature_flags
