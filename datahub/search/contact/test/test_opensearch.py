import pytest
from opensearch_dsl import Mapping

from datahub.search.contact import ContactSearchApp
from datahub.search.contact.models import Contact as SearchContact
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entities_query,
    limit_search_query,
)


def test_mapping(opensearch):
    """Test the OpenSearch mapping for a contact."""
    mapping = Mapping.from_opensearch(
        ContactSearchApp.search_model.get_write_index(),
    )

    assert mapping.to_dict() == {
        'properties': {
            '_document_type': {
                'type': 'keyword',
            },
            'address_1': {'type': 'text'},
            'address_2': {'type': 'text'},
            'address_country': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                },
                'type': 'object',
            },
            'address_area': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'normalizer': 'lowercase_asciifolding_normalizer', 'type': 'keyword'},
                },
                'type': 'object',
            },
            'address_county': {
                'normalizer': 'lowercase_asciifolding_normalizer',
                'type': 'keyword',
            },
            'address_postcode': {'type': 'text'},
            'address_same_as_company': {'type': 'boolean'},
            'address_town': {
                'normalizer': 'lowercase_asciifolding_normalizer',
                'type': 'keyword',
            },
            'adviser': {
                'properties': {
                    'first_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'id': {'type': 'keyword'},
                    'last_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'name': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'normalizer': 'lowercase_asciifolding_normalizer',
                                'type': 'keyword',
                            },
                            'trigram': {
                                'analyzer': 'trigram_analyzer',
                                'type': 'text',
                            },
                        },
                    },
                },
                'type': 'object',
            },
            'archived': {'type': 'boolean'},
            'archived_by': {
                'properties': {
                    'first_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'id': {'type': 'keyword'},
                    'last_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'name': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'normalizer': 'lowercase_asciifolding_normalizer',
                                'type': 'keyword',
                            },
                            'trigram': {
                                'analyzer': 'trigram_analyzer',
                                'type': 'text',
                            },
                        },
                    },
                },
                'type': 'object',
            },
            'archived_on': {'type': 'date'},
            'archived_reason': {'type': 'text'},
            'company': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'normalizer': 'lowercase_asciifolding_normalizer',
                                'type': 'keyword',
                            },
                            'trigram': {
                                'analyzer': 'trigram_analyzer',
                                'type': 'text',
                            },
                        },
                    },
                    'trading_names': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'analyzer': 'trigram_analyzer',
                                'type': 'text',
                            },
                        },
                    },
                },
                'type': 'object',
            },
            'company_sector': {
                'properties': {
                    'ancestors': {
                        'properties': {'id': {'type': 'keyword'}},
                        'type': 'object',
                    },
                    'id': {'type': 'keyword'},
                    'name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                },
                'type': 'object',
            },
            'company_uk_region': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                },
                'type': 'object',
            },
            'created_by': {
                'properties': {
                    'dit_team': {
                        'properties': {
                            'id': {'type': 'keyword'},
                            'name': {
                                'normalizer': 'lowercase_asciifolding_normalizer',
                                'type': 'keyword',
                            },
                        },
                        'type': 'object',
                    },
                    'first_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'id': {'type': 'keyword'},
                    'last_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'name': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'normalizer': 'lowercase_asciifolding_normalizer',
                                'type': 'keyword',
                            },
                            'trigram': {
                                'analyzer': 'trigram_analyzer',
                                'type': 'text',
                            },
                        },
                    },
                },
                'type': 'object',
            },
            'created_on': {'type': 'date'},
            'email': {
                'normalizer': 'lowercase_asciifolding_normalizer',
                'type': 'keyword',
            },
            'first_name': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                },
            },
            'full_telephone_number': {'type': 'keyword'},
            'id': {'type': 'keyword'},
            'job_title': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'trigram': {
                        'analyzer': 'trigram_analyzer',
                        'type': 'text',
                    },
                },
            },
            'last_name': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                },
            },
            'modified_on': {'type': 'date'},
            'name': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'trigram': {
                        'analyzer': 'trigram_analyzer',
                        'type': 'text',
                    },
                },
            },
            'name_with_title': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'trigram': {
                        'analyzer': 'trigram_analyzer',
                        'type': 'text',
                    },
                },
            },
            'notes': {
                'analyzer': 'english_analyzer',
                'type': 'text',
            },
            'primary': {'type': 'boolean'},
            'title': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                },
                'type': 'object',
            },
        },
        'dynamic': 'false',
    }


@pytest.mark.django_db
def test_get_basic_search_query():
    """Tests basic search query."""
    expected_query = {
        'query': {
            'bool': {
                'should': [
                    {
                        'match': {
                            'name.keyword': {
                                'query': 'test',
                                'boost': 2,
                            },
                        },
                    },
                    {
                        'multi_match': {
                            'query': 'test',
                            'fields': [
                                'address.area.name.trigram',
                                'address.country.name.trigram',
                                'address.county.trigram',
                                'address.line_1.trigram',
                                'address.line_2.trigram',
                                'address.postcode',
                                'address.town.trigram',
                                'address.trigram',
                                'address_country.name.trigram',
                                'address_postcode',
                                'companies.name',
                                'companies.name.trigram',
                                'company.name',
                                'company.name.trigram',
                                'company_number',
                                'contact.name',
                                'contact.name.trigram',
                                'contacts.name',
                                'contacts.name.trigram',
                                'country.trigram',
                                'dit_participants.adviser.name',
                                'dit_participants.adviser.name.trigram',
                                'dit_participants.team.name',
                                'dit_participants.team.name.trigram',
                                'email',
                                'event.name',
                                'event.name.trigram',
                                'event_type.name',
                                'event_type.name.trigram',
                                'export_segment',
                                'export_sub_segment',
                                'full_telephone_number',
                                'id',
                                'investor_company.name',
                                'investor_company.name.trigram',
                                'job_title',
                                'job_title.trigram',
                                'name',
                                'name.trigram',
                                'name_with_title',
                                'name_with_title.trigram',
                                'organiser.name.trigram',
                                'project_code',
                                'reference.trigram',
                                'reference_code',
                                'registered_address.area.name.trigram',
                                'registered_address.country.name.trigram',
                                'registered_address.county.trigram',
                                'registered_address.line_1.trigram',
                                'registered_address.line_2.trigram',
                                'registered_address.postcode',
                                'registered_address.town.trigram',
                                'related_programmes.name',
                                'related_programmes.name.trigram',
                                'sector.name',
                                'service.name',
                                'service.name.trigram',
                                'simpleton.name',
                                'subject',
                                'subject.english',
                                'subject.trigram',
                                'subtotal_cost.keyword',
                                'teams.name',
                                'teams.name.trigram',
                                'total_cost.keyword',
                                'trading_names',
                                'trading_names.trigram',
                                'uk_company.name',
                                'uk_company.name.trigram',
                                'uk_region.name',
                                'uk_region.name.trigram',
                            ],
                            'type': 'cross_fields',
                            'operator': 'and',
                        },
                    },
                ],
            },
        },
        'post_filter': {
            'bool': {
                'should': [
                    {
                        'term': {
                            '_document_type': 'contact',
                        },
                    },
                ],
            },
        },
        'aggs': {
            'count_by_type': {
                'terms': {
                    'field': '_document_type',
                },
            },
        },
        'from': 5,
        'size': 5,
        'sort': [
            '_score',
            'id',
        ],
        'track_total_hits': True,
    }

    query = get_basic_search_query(SearchContact, 'test', offset=5, limit=5)

    assert query.to_dict() == expected_query


@pytest.mark.django_db
def test_get_limited_search_by_entity_query():
    """Tests search by entity."""
    date = '2017-06-13T09:44:31.062870'
    filter_data = {
        'name': 'Woodside',
        'address_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'archived_before': date,
        'archived_after': date,
    }
    query = get_search_by_entities_query(
        [SearchContact],
        term='test',
        filter_data=filter_data,
    )
    query = limit_search_query(
        query,
        offset=5,
        limit=5,
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'name.keyword': {
                                            'query': 'test',
                                            'boost': 2,
                                        },
                                    },
                                }, {
                                    'multi_match': {
                                        'query': 'test',
                                        'fields': (
                                            'id',
                                            'name',
                                            'name.trigram',
                                            'name_with_title',
                                            'name_with_title.trigram',
                                            'email',
                                            'company.name',
                                            'company.name.trigram',
                                            'job_title',
                                            'job_title.trigram',
                                            'full_telephone_number',
                                        ),
                                        'type': 'cross_fields',
                                        'operator': 'and',
                                    },
                                },
                            ],
                        },
                    },
                ],
                'filter': [
                    {
                        'bool': {
                            'must': [
                                {
                                    'match': {
                                        'name': {
                                            'query': 'Woodside',
                                            'operator': 'and',
                                        },
                                    },
                                },
                                {
                                    'bool': {
                                        'should': [
                                            {
                                                'match': {
                                                    'address_country.id': {
                                                        'query':
                                                            '80756b9a-5d95-e211-a939-e4115bead28a',
                                                        'operator': 'and',
                                                    },
                                                },
                                            },
                                        ],
                                        'minimum_should_match': 1,
                                    },
                                }, {
                                    'range': {
                                        'archived': {
                                            'gte': '2017-06-13T09:44:31.062870',
                                            'lte': '2017-06-13T09:44:31.062870',
                                        },
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        },
        'sort': [
            '_score',
            'id',
        ],
        'track_total_hits': True,
        'from': 5,
        'size': 5,
    }
