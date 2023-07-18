import pytest


from datahub.company.test.factories import AdviserFactory
from datahub.search.adviser.apps import AdviserSearchApp

pytestmark = pytest.mark.django_db


def test_new_adviser_synced(opensearch_with_signals):
    """Test that new adviser is synced to OpenSearch."""
    adviser = AdviserFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=AdviserSearchApp.search_model.get_write_index(),
        id=adviser.pk,
    )


def test_updated_interaction_synced(opensearch_with_signals):
    """Test that when adviser is updated, it is synced to OpenSearch."""
    adviser = AdviserFactory(first_name='abc')
    adviser.first_name = 'def'

    adviser.save()
    opensearch_with_signals.indices.refresh()

    result = opensearch_with_signals.get(
        index=AdviserSearchApp.search_model.get_write_index(),
        id=adviser.pk,
    )

    assert result['_source'] == {
        '_document_type': AdviserSearchApp.name,
        'id': str(adviser.pk),
        'dit_team': {
            'id': str(adviser.dit_team.pk),
            'name': adviser.dit_team.name,
        },
        'is_active': adviser.is_active,
        'last_name': adviser.last_name,
        'first_name': adviser.first_name,
    }
