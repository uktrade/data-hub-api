import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.featureflag.test.factories import FeatureFlagFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestListFeatureFlags(APITestMixin):
    """Tests for listing of feature flags."""

    def test_can_list_feature_flags_having_no_permissions(self, api_client):
        """Should return 401"""
        url = reverse('api-v3:featureflag:collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_can_list_feature_flags(self):
        """List feature flags.."""
        feature_flags = FeatureFlagFactory.create_batch(2)
        url = reverse('api-v3:featureflag:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': str(feature_flags[1].pk),
                    'name': feature_flags[1].name,
                    'description': feature_flags[1].description,
                    'disabled_on': None,
                    'created_on': feature_flags[1].created_on.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'modified_on': feature_flags[1].modified_on.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'created_by': {
                        'first_name': feature_flags[1].created_by.first_name,
                        'last_name': feature_flags[1].created_by.last_name,
                        'name': feature_flags[1].created_by.name,
                        'id': str(feature_flags[1].created_by.pk)
                    },
                    'modified_by': {
                        'first_name': feature_flags[1].modified_by.first_name,
                        'last_name': feature_flags[1].modified_by.last_name,
                        'name': feature_flags[1].modified_by.name,
                        'id': str(feature_flags[1].modified_by.pk)
                    }
                }, {
                    'id': str(feature_flags[0].pk),
                    'name': feature_flags[0].name,
                    'description': feature_flags[0].description,
                    'disabled_on': None,
                    'created_on': feature_flags[0].created_on.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'modified_on': feature_flags[0].modified_on.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'created_by': {
                        'first_name': feature_flags[0].created_by.first_name,
                        'last_name': feature_flags[0].created_by.last_name,
                        'name': feature_flags[0].created_by.name,
                        'id': str(feature_flags[0].created_by.pk)
                    },
                    'modified_by': {
                        'first_name': feature_flags[0].modified_by.first_name,
                        'last_name': feature_flags[0].modified_by.last_name,
                        'name': feature_flags[0].modified_by.name,
                        'id': str(feature_flags[0].modified_by.pk)
                    }
                }
            ]
        }
