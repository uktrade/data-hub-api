from unittest.mock import patch, Mock

from django.conf import settings
from django.urls import reverse
from elasticsearch import Elasticsearch
from rest_framework.test import APIRequestFactory

from search.views import Search


@patch('search.views.search_by_term')
@patch('search.views.get_elasticsearch_client')
def test_search_by_term(mocked_get_es_client, mocked_search_by_term):
    mocked_client = Mock(spec_set=Elasticsearch)
    mocked_get_es_client.return_value = mocked_client
    mocked_search_by_term.return_value.hits.hits = [
        {
            '_id': 1,
            '_type': 'company',
            '_source': {'name': 'Foo'}
        },
        {
            '_id': 2,
            '_type': 'company',
            '_source': {'name': 'Foo test'}
        }
    ]

    url = reverse('search')
    factory = APIRequestFactory()
    request = factory.post(
        url,
        {'term': 'Foo'}
    )
    response = Search.as_view()(request)

    expected_response = [
        {'id': 1, 'type': 'company', 'name': 'Foo'},
        {'id': 2, 'type': 'company', 'name': 'Foo test'}
    ]
    assert response.data == expected_response
    mocked_search_by_term.assert_called_with(
        client=mocked_client,
        index=settings.ES_INDEX,
        limit=100,
        offset=0,
        term='Foo'
    )
