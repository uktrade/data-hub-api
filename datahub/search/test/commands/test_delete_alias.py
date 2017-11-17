from unittest import mock

import pytest
from django.core import management

from datahub.search.management.commands import delete_alias


pytestmark = pytest.mark.django_db


@mock.patch('datahub.search.management.commands.delete_alias.connections.get_connection')
def test_delete_alias(get_connection):
    """Tests creating alias for Elasticsearch index."""
    es = get_connection.return_value

    current_index = 'test_index'
    alias_name = 'test_index_alias'

    management.call_command(delete_alias.Command(),
                            current_index=current_index,
                            alias_name=alias_name)

    es.indices.delete_alias.assert_called_with(
        index=current_index,
        name=alias_name,
    )
