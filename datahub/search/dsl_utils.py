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
        'name': SortableCaseInsensitiveKeywordText(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramText(),
    }

    if include_dit_team:
        props['dit_team'] = id_name_mapping()
    return Nested(
        properties=props,
        include_in_parent=True,
    )


def contact_or_adviser_partial_mapping(field):
    """Mapping for Adviser/Contact fields that allows partial matching."""
    props = {
        'id': Keyword(),
        'first_name': SortableCaseInsensitiveKeywordText(),
        'last_name': SortableCaseInsensitiveKeywordText(),
        'name': SortableCaseInsensitiveKeywordText(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramText(),
    }
    return Nested(
        properties=props,
        include_in_parent=True,
    )


def id_name_mapping():
    """Mapping for id name fields."""
    return Nested(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(),
        },
        include_in_parent=True,
    )


def id_name_partial_mapping(field):
    """Mapping for id name fields."""
    return Nested(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(copy_to=f'{field}.name_trigram'),
            'name_trigram': TrigramText(),
        },
        include_in_parent=True,
    )


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


def sector_mapping():
    """Mapping for sector fields."""
    return Nested(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(),
            'ancestors': _ancestor_sector_mapping(),
        },
        include_in_parent=True,
    )


def _ancestor_sector_mapping():
    """Mapping for ancestral sector fields."""
    return Nested(
        properties={
            'id': Keyword(),
        },
        include_in_parent=True,
    )
