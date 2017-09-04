from functools import partial
from elasticsearch_dsl import Keyword, Nested, String

SortableCaseInsensitiveKeywordString = partial(
    String,
    analyzer='lowercase_keyword_analyzer',
    fielddata=True
)
TrigramString = partial(String, analyzer='trigram_analyzer')
EnglishString = partial(String, analyzer='english_analyzer')
SortableString = partial(String, fielddata=True)


def contact_or_adviser_mapping(field, include_dit_team=False):
    """Mapping for Adviser/Contact fields."""
    props = {
        'id': Keyword(),
        'first_name': SortableCaseInsensitiveKeywordString(),
        'last_name': SortableCaseInsensitiveKeywordString(),
        'name': SortableCaseInsensitiveKeywordString(),
    }

    if include_dit_team:
        props['dit_team'] = id_name_mapping()
    return Nested(properties=props)


def contact_or_adviser_partial_mapping(field):
    """Mapping for Adviser/Contact fields that allows partial matching."""
    props = {
        'id': Keyword(),
        'first_name': SortableCaseInsensitiveKeywordString(),
        'last_name': SortableCaseInsensitiveKeywordString(),
        'name': SortableCaseInsensitiveKeywordString(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramString(),
    }
    return Nested(properties=props)


def id_name_mapping():
    """Mapping for id name fields."""
    return Nested(properties={
        'id': Keyword(),
        'name': SortableCaseInsensitiveKeywordString(),
    })


def id_name_partial_mapping(field):
    """Mapping for id name fields."""
    return Nested(properties={
        'id': Keyword(),
        'name': SortableCaseInsensitiveKeywordString(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramString(),
    })


def id_uri_mapping():
    """Mapping for id uri fields."""
    return Nested(properties={
        'id': Keyword(),
        'uri': SortableCaseInsensitiveKeywordString()
    })


def company_mapping():
    """Mapping for id company_number fields."""
    return Nested(properties={
        'id': Keyword(),
        'company_number': SortableCaseInsensitiveKeywordString()
    })
