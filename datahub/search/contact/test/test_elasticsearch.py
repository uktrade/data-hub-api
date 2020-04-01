from elasticsearch_dsl import Mapping

from datahub.search.contact import ContactSearchApp
from datahub.search.contact.models import Contact as ESContact
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entities_query,
    limit_search_query,
)


def test_mapping(es):
    """Test the ES mapping for a contact."""
    mapping = Mapping.from_es(
        ContactSearchApp.es_model.get_write_index(),
        ContactSearchApp.name,
    )

    assert mapping.to_dict() == {
        'contact': {
            'properties': {
                '_document_type': {
                    'type': 'keyword',
                },
                'accepts_dit_email_marketing': {'type': 'boolean'},
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
                'email_alternative': {'type': 'text'},
                'first_name': {
                    'type': 'text',
                    'fields': {
                        'keyword': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                },
                'id': {'type': 'keyword'},
                'job_title': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
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
                'notes': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'primary': {'type': 'boolean'},
                'telephone_alternative': {'type': 'text'},
                'telephone_countrycode': {'type': 'keyword'},
                'telephone_number': {'type': 'keyword'},
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
        },
    }


def test_get_basic_search_query():
    """Tests basic search query."""
    query = get_basic_search_query(ESContact, 'test', offset=5, limit=5)

    assert query.to_dict() == {
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
                                'address.country.name.trigram',
                                'address.postcode.trigram',
                                'address_country.name.trigram',
                                'address_postcode.trigram',
                                'company.name',
                                'company.name.trigram',
                                'company_number',
                                'contact.name',
                                'contact.name.trigram',
                                'contacts.name',
                                'contacts.name.trigram',
                                'dit_participants.adviser.name',
                                'dit_participants.adviser.name.trigram',
                                'dit_participants.team.name',
                                'dit_participants.team.name.trigram',
                                'email',
                                'email_alternative',
                                'event.name',
                                'event.name.trigram',
                                'id',
                                'investor_company.name',
                                'investor_company.name.trigram',
                                'name',
                                'name.trigram',
                                'organiser.name.trigram',
                                'project_code.trigram',
                                'reference.trigram',
                                'reference_code',
                                'registered_address.country.name.trigram',
                                'registered_address.postcode.trigram',
                                'related_programmes.name',
                                'related_programmes.name.trigram',
                                'simpleton.name',
                                'subject.english',
                                'subtotal_cost.keyword',
                                'teams.name',
                                'teams.name.trigram',
                                'total_cost.keyword',
                                'trading_names',
                                'trading_names.trigram',
                                'uk_company.name',
                                'uk_company.name.trigram',
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
    }


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
        [ESContact],
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
                                            'email',
                                            'email_alternative',
                                            'company.name',
                                            'company.name.trigram',
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
        'from': 5,
        'size': 5,
    }
