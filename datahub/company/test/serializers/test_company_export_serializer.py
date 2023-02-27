from unittest.mock import Mock

import pytest
from rest_framework import serializers

from datahub.company.serializers import CompanyExportSerializer
from datahub.company.test.factories import AdviserFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestCompanyExportSerializer:
    def test_serializer_validation(self):
        request = Mock()
        data = {'team_members': [advisor.id for advisor in AdviserFactory.create_batch(6)]}
        serializer = CompanyExportSerializer(data=data, context={'request': request})

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert dict(excinfo.value.detail)['team_members'] == ['You can only add 5 team members']
