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
                    },
                    {
                        'match_phrase': {
                            'id': {
                                'query': 'test'
                            }
                        }
                    },
                    {
                        'match': {
                            'name': {
                                'query': 'test'
                            }
                        }
                    },
                    {
                        'match_phrase': {
                            'name_trigram': {
                                'query': 'test'
                            }
                        }
                    },
                    {
                        'match': {
                            'address_1': 'test'
                        }
                    },
                    {
                        'match': {
                            'address_2': 'test'
                        }
                    },
                    {
                        'nested': {
                            'path': 'address_country',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'address_country.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'match': {
                            'address_county': 'test'
                        }
                    },
                    {
                        'match': {
                            'address_town': 'test'
                        }
                    },
                    {
                        'nested': {
                            'path': 'business_activities',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'business_activities.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'classification',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'classification.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'company',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'company.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'match': {
                            'email': 'test'
                        }
                    },
                    {
                        'nested': {
                            'path': 'export_to_countries',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'export_to_countries.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'future_interest_countries',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'future_interest_countries.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'intermediate_company',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'intermediate_company.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'investor_company',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'investor_company.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'match': {
                            'notes': 'test'
                        }
                    },
                    {
                        'nested': {
                            'path': 'registered_address_country',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'registered_address_country.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'match': {
                            'registered_address_town': 'test'
                        }
                    },
                    {
                        'nested': {
                            'path': 'sector',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'sector.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'trading_address_country',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'trading_address_country.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'match': {
                            'trading_address_town': 'test'
                        }
                    },
                    {
                        'nested': {
                            'path': 'uk_company',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'uk_company.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'nested': {
                            'path': 'uk_region',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'uk_region.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'match': {
                            'website': 'test'
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


def test_get_search_by_entity_query():
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
        offset=5,
        limit=5
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
                                        'id': {
                                            'query': 'test'
                                        }
                                    }
                                }, {
                                    'match': {
                                        'name': {
                                            'query': 'test'
                                        }
                                    }
                                }, {
                                    'match_phrase': {
                                        'name_trigram': {
                                            'query': 'test'
                                        }
                                    }
                                }, {
                                    'match': {
                                        'address_1': 'test'
                                    }
                                }, {
                                    'match': {
                                        'address_2': 'test'
                                    }
                                }, {
                                    'nested': {
                                        'path': 'address_country',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'address_country.name': 'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'match': {
                                        'address_county': 'test'
                                    }
                                }, {
                                    'match': {
                                        'address_town': 'test'
                                    }
                                }, {
                                    'nested': {
                                        'path': 'company',
                                        'query': {
                                            'bool': {
                                                'must': [{
                                                    'match': {
                                                        'company.name': 'test'
                                                    }
                                                }]
                                            }
                                        }
                                    }
                                }, {
                                    'match': {
                                        'email': 'test'
                                    }
                                }, {
                                    'match': {
                                        'notes': 'test'
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
                'must': [{
                    'bool': {
                        'should': [{'term': {'address_town': 'Woodside'}}],
                        'minimum_should_match': 1
                    }
                }, {
                    'bool': {
                        'should': [{
                            'nested': {
                                'path': 'trading_address_country',
                                'query': {
                                    'term': {
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
                }]
            }
        },
        'from': 5,
        'size': 5
    }
