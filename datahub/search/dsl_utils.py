from functools import partial
from elasticsearch_dsl import Nested, String


KeywordString = partial(String, index='not_analyzed')
CaseInsensitiveKeywordString = partial(String, analyzer='lowercase_keyword_analyzer')
TrigramString = partial(String, analyzer='trigram_analyzer')
EnglishString = partial(String, analyzer='english_analyzer')


def contact_or_adviser_mapping(field, include_dit_team=False):
    """Mapping for Adviser/Contact fields."""
    props = {
        'id': KeywordString(),
        'first_name': CaseInsensitiveKeywordString(),
        'last_name': CaseInsensitiveKeywordString(),
        'name': CaseInsensitiveKeywordString(),
    }

    if include_dit_team:
        props['dit_team'] = id_name_mapping()
    return Nested(properties=props)


def contact_or_adviser_partial_mapping(field):
    """Mapping for Adviser/Contact fields that allows partial matching."""
    props = {
        'id': KeywordString(),
        'first_name': CaseInsensitiveKeywordString(),
        'last_name': CaseInsensitiveKeywordString(),
        'name': CaseInsensitiveKeywordString(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramString(),
    }
    return Nested(properties=props)


def id_name_mapping():
    """Mapping for id name fields."""
    return Nested(properties={
        'id': KeywordString(),
        'name': CaseInsensitiveKeywordString(),
    })


def id_name_partial_mapping(field):
    """Mapping for id name fields."""
    return Nested(properties={
        'id': KeywordString(),
        'name': CaseInsensitiveKeywordString(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramString(),
    })


def id_uri_mapping():
    """Mapping for id uri fields."""
    return Nested(properties={
        'id': KeywordString(),
        'uri': CaseInsensitiveKeywordString()
    })


def company_mapping():
    """Mapping for id company_number fields."""
    return Nested(properties={
        'id': KeywordString(),
        'company_number': CaseInsensitiveKeywordString()
    })
