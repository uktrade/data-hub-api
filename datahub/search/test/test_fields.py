from random import shuffle

import pytest
from django.urls import reverse

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.search.fields import address_field
from datahub.search.sync_object import sync_object
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp


class TestNormalizedField(APITestMixin):
    """Tests the behaviour of NormalizedKeyword."""

    def test_sorting(self, es):
        """Test to demonstrate how NormalizedKeyword sorts."""
        names = [
            'Alice',
            'Barbara',
            'barbara 2',
            'Álice 2',
            'ａlice 3',
        ]
        shuffle(names)

        for name in names:
            obj = SimpleModel(name=name)
            obj.save()
            sync_object(SimpleModelSearchApp, obj.pk)

        es.indices.refresh()

        user = create_test_user(permission_codenames=['view_simplemodel'])
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:simplemodel')

        response = api_client.post(
            url,
            data={
                'sortby': 'name',
            },
        )
        response_data = response.json()
        results = response_data['results']

        assert [result['name'] for result in results] == [
            'Alice',
            'Álice 2',
            'ａlice 3',
            'Barbara',
            'barbara 2',
        ]


@pytest.mark.parametrize(
    'index_country, index_area, expected_mapping',
    (
        (
            True,
            True,
            {
                'type': 'object',
                'properties': {
                    'line_1': {'index': False, 'type': 'text'},
                    'line_2': {'index': False, 'type': 'text'},
                    'town': {'index': False, 'type': 'text'},
                    'county': {'index': False, 'type': 'text'},
                    'postcode': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'area': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'name': {
                                'type': 'text',
                                'fields': {
                                    'trigram': {
                                        'type': 'text',
                                        'analyzer': 'trigram_analyzer',
                                    },
                                },
                            },
                        },
                    },
                    'country': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'name': {
                                'type': 'text',
                                'fields': {
                                    'trigram': {
                                        'type': 'text',
                                        'analyzer': 'trigram_analyzer',
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ),

        (
            False,
            False,
            {
                'type': 'object',
                'properties': {
                    'line_1': {'index': False, 'type': 'text'},
                    'line_2': {'index': False, 'type': 'text'},
                    'town': {'index': False, 'type': 'text'},
                    'county': {'index': False, 'type': 'text'},
                    'postcode': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'area': {
                        'type': 'object',
                        'properties': {
                            'id': {'index': False, 'type': 'keyword'},
                            'name': {'index': False, 'type': 'text'},
                        },
                    },
                    'country': {
                        'type': 'object',
                        'properties': {
                            'id': {'index': False, 'type': 'keyword'},
                            'name': {'index': False, 'type': 'text'},
                        },
                    },
                },
            },
        ),
    ),
)
def test_address_field(index_country, index_area, expected_mapping):
    """Test for address_field."""
    field_mapping = address_field(index_country=index_country, index_area=index_area)
    assert field_mapping.to_dict() == expected_mapping
