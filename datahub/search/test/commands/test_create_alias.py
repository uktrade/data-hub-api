from unittest import mock

import pytest
from django.core import management

from datahub.search.management.commands import create_alias


pytestmark = pytest.mark.django_db


@mock.patch('datahub.search.management.commands.create_alias.connections.get_connection')
def test_create_alias(get_connection):
    """Tests creating alias for Elasticsearch index."""
    es = get_connection.return_value

    current_index = 'test_index'
    alias_name = 'test_index_alias'

    management.call_command(create_alias.Command(),
                            current_index=current_index,
                            alias_name=alias_name)

    es.indices.put_alias.assert_called_with(
        index=current_index,
        name=alias_name,
    )
