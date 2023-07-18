import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.search.adviser import AdviserSearchApp
from datahub.search.adviser.models import Adviser

pytestmark = pytest.mark.django_db


def test_adviser_to_dict(opensearch):
    """Test for adviser search model"""
    adviser = AdviserFactory()
    result = Adviser.db_object_to_dict(adviser)

    assert result == {
        '_document_type': AdviserSearchApp.name,
        'dit_team': {
            'id': str(adviser.dit_team.pk),
            'name': adviser.dit_team.name,
        },
        'id': adviser.id,
        'is_active': adviser.is_active,
        'last_name': adviser.last_name,
        'first_name': adviser.first_name,
    }
