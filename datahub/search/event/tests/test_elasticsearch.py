from elasticsearch_dsl import Mapping

from datahub.search.event import EventSearchApp


def test_mapping(setup_es):
    """Test the ES mapping for an event."""
    mapping = Mapping.from_es(
        EventSearchApp.es_model.get_write_index(),
        EventSearchApp.name,
    )

    assert mapping.to_dict() == {
        'event': {
            'dynamic': 'false',
            'properties': {
                'address_1': {'type': 'text'},
                'address_2': {'type': 'text'},
                'address_country': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': [
                                'address_country.name_trigram',
                            ],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'address_county': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
                },
                'address_postcode': {
                    'copy_to': [
                        'address_postcode_trigram',
                    ],
                    'type': 'text',
                },
                'address_postcode_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'address_town': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
                },
                'created_on': {'type': 'date'},
                'disabled_on': {'type': 'date'},
                'end_date': {'type': 'date'},
                'event_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'id': {'type': 'keyword'},
                'lead_team': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'location_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'modified_on': {'type': 'date'},
                'name': {
                    'copy_to': [
                        'name_keyword',
                        'name_trigram',
                    ],
                    'fielddata': True,
                    'type': 'text',
                },
                'name_keyword': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
                },
                'name_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'notes': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'organiser': {
                    'properties': {
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': [
                                'organiser.name_trigram',
                            ],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'related_programmes': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': [
                                'related_programmes.name_trigram',
                            ],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'service': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'start_date': {'type': 'date'},
                'teams': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': [
                                'teams.name_trigram',
                            ],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'uk_region': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': [
                                'uk_region.name_trigram',
                            ],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
            },
        },
    }
