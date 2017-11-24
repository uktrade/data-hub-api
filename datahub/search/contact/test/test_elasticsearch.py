from ..models import Contact as ESContact

from ... import elasticsearch


def test_get_basic_search_query():
    """Tests basic search query."""
    query = elasticsearch.get_basic_search_query('test', entities=(ESContact,), offset=5, limit=5)

    assert query.to_dict() == {
        'query': {
            'bool': {
                'should': [
                    {
                        'match_phrase': {
                            'name_keyword': {
                                'query': 'test',
                                'boost': 2
                            }
                        }
                    }, {
                        'match_phrase': {
                            'id': 'test'
                        }
                    }, {
                        'multi_match': {
                            'query': 'test',
                            'fields': [
                                'address_country.name_trigram',
                                'address_postcode_trigram',
                                'company.name_trigram',
                                'company_number',
                                'contact.name_trigram',
                                'dit_adviser.name_trigram',
                                'dit_team.name_trigram',
                                'email',
                                'email_alternative',
                                'event.name_trigram',
                                'investor_company.name_trigram',
                                'name_trigram',
                                'organiser.name_trigram',
                                'project_code_trigram',
                                'reference_code',
                                'reference_trigram',
                                'registered_address_country.name_trigram',
                                'registered_address_postcode_trigram',
                                'related_programmes.name_trigram',
                                'sector.name_trigram',
                                'subject_english',
                                'subtotal_cost_string',
                                'teams.name_trigram',
                                'total_cost_string',
                                'trading_address_country.name_trigram',
                                'trading_address_postcode_trigram',
                                'trading_name_trigram',
                                'uk_company.name_trigram',
                                'uk_region.name_trigram'
                            ],
                            'type': 'cross_fields',
                            'operator': 'and'
                        }
                    }
                ]
            }
        },
        'post_filter': {
            'bool': {
                'should': [
                    {
                        'term': {
                            '_type': 'contact'
                        }
                    }
                ]
            }
        },
        'aggs': {
            'count_by_type': {
                'terms': {
                    'field': '_type'
                }
            }
        },
        'from': 5,
        'size': 5
    }


def test_get_limited_search_by_entity_query():
    """Tests search by entity."""
    date = '2017-06-13T09:44:31.062870'
    filters = {
        'address_town': ['Woodside'],
        'trading_address_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
    }
    ranges = {
        'estimated_land_date': {
            'gte': date,
            'lte': date
        }
    }
    query = elasticsearch.get_search_by_entity_query(
        term='test',
        filters=filters,
        ranges=ranges,
        entity=ESContact,
    )
    query = elasticsearch.limit_search_query(
        query,
        offset=5,
        limit=5,
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            '_type': 'contact'
                        }
                    }, {
                        'bool': {
                            'should': [
                                {
                                    'match_phrase': {
                                        'name_keyword': {
                                            'query': 'test',
                                            'boost': 2
                                        }
                                    }
                                }, {
                                    'match_phrase': {
                                        'id': 'test'
                                    }
                                }, {
                                    'multi_match': {
                                        'query': 'test',
                                        'fields': (
                                            'name_trigram',
                                            'email',
                                            'email_alternative',
                                            'company.name_trigram'
                                        ),
                                        'type': 'cross_fields',
                                        'operator': 'and'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        'post_filter': {
            'bool': {
                'must': [
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'address_town': {
                                            'query': 'Woodside',
                                            'operator': 'and'
                                        }
                                    }
                                }
                            ],
                            'minimum_should_match': 1
                        }
                    }, {
                        'bool': {
                            'should': [{
                                'nested': {
                                    'path': 'trading_address_country',
                                    'query': {
                                        'match_phrase': {
                                            'trading_address_country.id':
                                                '80756b9a-5d95-e211-a939-e4115bead28a'
                                        }
                                    }
                                }
                            }],
                            'minimum_should_match': 1
                        }
                    }, {
                        'range': {
                            'estimated_land_date': {
                                'gte': '2017-06-13T09:44:31.062870',
                                'lte': '2017-06-13T09:44:31.062870'
                            }
                        }
                    }
                ]
            }
        },
        'from': 5,
        'size': 5
    }
