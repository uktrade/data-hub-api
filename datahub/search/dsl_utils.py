from functools import partial
from elasticsearch_dsl import Keyword, Nested, Text

SortableCaseInsensitiveKeywordText = partial(
    Text,
    analyzer='lowercase_keyword_analyzer',
    fielddata=True
)
TrigramText = partial(Text, analyzer='trigram_analyzer')
SortableTrigramText = partial(Text, analyzer='trigram_analyzer', fielddata=True)
EnglishText = partial(Text, analyzer='english_analyzer')
SortableText = partial(Text, fielddata=True)


def contact_or_adviser_mapping(field, include_dit_team=False):
    """Mapping for Adviser/Contact fields."""
    props = {
        'id': Keyword(),
        'first_name': SortableCaseInsensitiveKeywordText(),
        'last_name': SortableCaseInsensitiveKeywordText(),
        'name': SortableCaseInsensitiveKeywordText(),
    }

    if include_dit_team:
        props['dit_team'] = id_name_mapping()
    return Nested(properties=props)


def contact_or_adviser_partial_mapping(field, name_params=None):
    """Mapping for Adviser/Contact fields that allows partial matching."""
    if not name_params:
        name_params = {}

    copy_to = f'{field}.name_trigram'
    if 'copy_to' in name_params:
        if isinstance(name_params['copy_to'], list):
            name_params['copy_to'].append(copy_to)
        else:
            name_params['copy_to'] = [name_params['copy_to'], copy_to]
    else:
        name_params['copy_to'] = copy_to

    props = {
        'id': Keyword(),
        'first_name': SortableCaseInsensitiveKeywordText(),
        'last_name': SortableCaseInsensitiveKeywordText(),
        'name': SortableCaseInsensitiveKeywordText(**name_params),
        'name_trigram': SortableTrigramText(),
    }
    return Nested(properties=props)


def id_name_mapping(name_params=None):
    """Mapping for id name fields."""
    if not name_params:
        name_params = {}

    return Nested(properties={
        'id': Keyword(),
        'name': SortableCaseInsensitiveKeywordText(**name_params),
    })


def id_name_partial_mapping(field, name_params=None):
    """Mapping for id name fields."""
    if not name_params:
        name_params = {}

    copy_to = f'{field}.name_trigram'
    if 'copy_to' in name_params:
        if isinstance(name_params['copy_to'], list):
            name_params['copy_to'].append(copy_to)
        else:
            name_params['copy_to'] = [name_params['copy_to'], copy_to]
    else:
        name_params['copy_to'] = copy_to

    return Nested(properties={
        'id': Keyword(),
        'name': SortableCaseInsensitiveKeywordText(**name_params),
        'name_trigram': SortableTrigramText(),
    })


def id_uri_mapping():
    """Mapping for id uri fields."""
    return Nested(properties={
        'id': Keyword(),
        'uri': SortableCaseInsensitiveKeywordText()
    })


def company_mapping():
    """Mapping for id company_number fields."""
    return Nested(properties={
        'id': Keyword(),
        'company_number': SortableCaseInsensitiveKeywordText()
    })


def investment_project_mapping():
    """Mapping for investment project relations."""
    return Nested(properties={
        'id': Keyword(),
        'name': SortableCaseInsensitiveKeywordText(),
        'project_code': SortableCaseInsensitiveKeywordText(),
    })
