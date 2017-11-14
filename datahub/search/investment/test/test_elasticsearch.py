from ..models import InvestmentProject as ESInvestmentProject

from ... import elasticsearch


def test_get_basic_search_query():
    """Tests basic search query."""
    query = elasticsearch.get_basic_search_query(
        'test', entities=(ESInvestmentProject,), offset=5, limit=5
    )

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
                        'match': {
                            'name': {
                                'query': 'test',
                                'operator': 'and'
                            }
                        }
                    }, {
                        'match': {
                            'name_trigram': {
                                'query': 'test',
                                'operator': 'and'
                            }
                        }
                    }, {
                        'match': {
                            'global_search': {
                                'query': 'test',
                                'operator': 'and'
                            }
                        }
                    }, {
                        'match': {
                            'subtotal_cost_string': {
                                'query': 'test',
                                'operator': 'and'
                            }
                        }
                    }, {
                        'match': {
                            'total_cost_string': {
                                'query': 'test',
                                'operator': 'and'
                            }
                        }
                    }
                ]
            }
        },
        'post_filter': {
            'bool': {
                'should': [{
                    'term': {
                        '_type': 'investment_project'
                    }
                }]
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


def test_limited_get_search_by_entity_query():
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
        entity=ESInvestmentProject,
    )
    query = elasticsearch.limit_search_query(
        query,
        offset=5,
        limit=5
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            '_type': 'investment_project'
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
                                    'match': {
                                        'name': {
                                            'query': 'test',
                                            'operator': 'and'
                                        }
                                    }
                                }, {
                                    'match': {
                                        'name_trigram': {
                                            'query': 'test',
                                            'operator': 'and'
                                        }
                                    }
                                }, {
                                    'match': {
                                        'global_search': {
                                            'query': 'test',
                                            'operator': 'and'
                                        }
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
                        'should': [
                            {
                                'nested': {
                                    'path': 'trading_address_country',
                                    'query': {
                                        'match_phrase': {
                                            'trading_address_country.id':
                                                '80756b9a-5d95-e211-a939-e4115bead28a'
                                        }
                                    }
                                }
                            }
                        ],
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
