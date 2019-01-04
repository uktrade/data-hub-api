from functools import partial

from elasticsearch_dsl import Keyword, Object, Text

from datahub.search.elasticsearch import lowercase_asciifolding_normalizer

# Keyword with normalisation to improve sorting (by keeping e, E, è, ê etc. together).
# This should be used in preference to SortableCaseInsensitiveKeywordText
NormalizedKeyword = partial(
    Keyword,
    normalizer=lowercase_asciifolding_normalizer,
)
# Avoid using as this uses fielddata=True. NormalizedKeyword will have better behaviour
# for sorting
SortableCaseInsensitiveKeywordText = partial(
    Text,
    analyzer='lowercase_keyword_analyzer',
    fielddata=True,
)
TrigramText = partial(Text, analyzer='trigram_analyzer')
SortableTrigramText = partial(Text, analyzer='trigram_analyzer', fielddata=True)
EnglishText = partial(Text, analyzer='english_analyzer')
SortableText = partial(Text, fielddata=True)


class TextWithKeyword(Text):
    """
    Text field with keyword sub-field.

    This definition is in line with the data type Elasticsearch uses for dynamically mapped text
    fields, and is intended to be used to explicitly define fields that were previously
    implicitly added to the ES mapping.
    """

    # The default value Elasticsearch uses for ignore_above when dynamically mapping text fields
    ES_DEFAULT_IGNORE_ABOVE = 256

    def __init__(self, *args, **kwargs):
        """Initialises the field, creating a keyword sub-field."""
        super().__init__(
            *args,
            **kwargs,
            fields={
                'keyword': Keyword(ignore_above=self.ES_DEFAULT_IGNORE_ABOVE),
            },
        )


def contact_or_adviser_field(field, include_dit_team=False):
    """Object field for advisers and contacts."""
    props = {
        'id': Keyword(),
        'first_name': SortableCaseInsensitiveKeywordText(),
        'last_name': SortableCaseInsensitiveKeywordText(),
        'name': SortableCaseInsensitiveKeywordText(copy_to=f'{field}.name_trigram'),
        'name_trigram': TrigramText(),
    }

    if include_dit_team:
        props['dit_team'] = id_name_field()

    return Object(properties=props)


def id_name_field():
    """Object field with id and name sub-fields."""
    return Object(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(),
        },
    )


def id_name_partial_field(field):
    """Object field with id and name sub-fields, and with partial matching on name."""
    return Object(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(copy_to=f'{field}.name_trigram'),
            'name_trigram': TrigramText(),
        },
    )


def company_field(field):
    """Company field."""
    return Object(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(copy_to=f'{field}.name_trigram'),
            'name_trigram': TrigramText(),
            'trading_name': Keyword(index=False),
            'trading_names': Text(
                copy_to=f'{field}.trading_names_trigram',
            ),
            'trading_names_trigram': TrigramText(),
        },
    )


def ch_company_field():
    """Object field with id and company_number sub-fields."""
    return Object(properties={
        'id': Keyword(),
        'company_number': SortableCaseInsensitiveKeywordText(),
    })


def sector_field():
    """Sector field."""
    ancestors = Object(
        properties={
            'id': Keyword(),
        },
    )

    return Object(
        properties={
            'id': Keyword(),
            'name': SortableCaseInsensitiveKeywordText(),
            'ancestors': ancestors,
        },
    )


def object_field(*fields):
    """This is a mapping that reflects how Elasticsearch auto-creates mappings for objects."""
    return Object(
        properties={field: TextWithKeyword() for field in fields},
    )
