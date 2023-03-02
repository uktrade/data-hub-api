from unittest.mock import Mock

import pytest
from rest_framework import serializers

from datahub.company.serializers import CompanyExportSerializer
from datahub.company.test.factories import AdviserFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestCompanyExportSerializer:
    """Tests for the Company Export Serializer"""

    def test_export_team_members_validation_throws_error_for_more_than_allowed_max(self):
        """
        Test the team_members field is validated by the serializer and an error thrown when the
        number of team_members provided is above the max allowed
        """
        request = Mock()
        data = {'team_members': [advisor.id for advisor in AdviserFactory.create_batch(6)]}
        serializer = CompanyExportSerializer(data=data, context={'request': request})

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert dict(excinfo.value.detail)['team_members'] == ['You can only add 5 team members']
