import json
from io import StringIO
from unittest import mock

import pytest
from django.core import management


from datahub.search.management.commands import get_alias


pytestmark = pytest.mark.django_db


@mock.patch('datahub.search.management.commands.delete_alias.connections.get_connection')
def test_get_alias(get_connection):
    """Tests creating alias for Elasticsearch index."""
    es = get_connection.return_value

    current_index = 'test_index'

    aliases = {
        'test_index': {
            'aliases': {
                'test_alias': {}
            }
        }
    }

    es.indices.get_alias.return_value = aliases

    out = StringIO()
    management.call_command(get_alias.Command(), current_index=current_index, stdout=out)

    es.indices.get_alias.assert_called_with(
        index=current_index,
    )

    result = json.loads(out.getvalue())

    assert aliases == result
