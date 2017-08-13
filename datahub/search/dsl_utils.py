from functools import partial
from elasticsearch_dsl import Nested, String


KeywordString = partial(String, index='not_analyzed')
CaseInsensitiveKeywordString = partial(String, analyzer='lowercase_keyword_analyzer')
TrigramString = partial(String, analyzer='trigram_analyzer')


def _contact_mapping(field):
    """Mapping for Adviser/Contact fields."""
    return Nested(properties={'id': KeywordString(),
                              'first_name': String(copy_to=f'{field}.name'),
                              'last_name': String(copy_to=f'{field}.name'),
                              'name': CaseInsensitiveKeywordString(),
                              })


def _id_name_mapping():
    """Mapping for id name fields."""
    return Nested(properties={
        'id': KeywordString(),
        'name': CaseInsensitiveKeywordString()
    })


def _id_uri_mapping():
    """Mapping for id uri fields."""
    return Nested(properties={
        'id': KeywordString(),
        'uri': CaseInsensitiveKeywordString()
    })


def _company_mapping():
    """Mapping for id company_number fields."""
    return Nested(properties={
        'id': KeywordString(),
        'company_number': CaseInsensitiveKeywordString()
    })
