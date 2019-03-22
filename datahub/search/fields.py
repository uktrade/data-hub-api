from functools import partial

from elasticsearch_dsl import Keyword, Object, Text

from datahub.search.elasticsearch import lowercase_asciifolding_normalizer

# Keyword with normalisation to improve sorting (by keeping e, E, è, ê etc. together).
NormalizedKeyword = partial(
    Keyword,
    normalizer=lowercase_asciifolding_normalizer,
)
TrigramText = partial(Text, analyzer='trigram_analyzer')
EnglishText = partial(Text, analyzer='english_analyzer')


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
        'first_name': NormalizedKeyword(),
        'last_name': NormalizedKeyword(),
        'name': NormalizedKeyword(copy_to=f'{field}.name_trigram'),
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
            'name': NormalizedKeyword(),
        },
    )


def id_unindexed_name_field():
    """Object field with id and unindexed name sub-fields."""
    return Object(
        properties={
            'id': Keyword(),
            'name': Keyword(index=False),
        },
    )


def id_name_partial_field(field):
    """
    Object field with id and name sub-fields, and with partial matching on name.

    The `name` field is being migrated away from using `copy_to` to being a multi-field.
    `name_trigram` and `name.trigram` are both defined while the switch takes place.

    Additionally, the `name` field should have had a data type of text, but it was mistakenly made
    a keyword field. Hence, a `keyword` sub-field has also been added so type of `name` can be
    changed to text once sorting operations have been migrated to using the `keyword` sub-field.

    TODO:
        - remove name_trigram once related logic has been updated to use name.trigram
        - change name use Text instead of NormalizedKeyword once sorting options have been
        updated to use name.keyword
    """
    return Object(
        properties={
            'id': Keyword(),
            'name': NormalizedKeyword(
                copy_to=f'{field}.name_trigram',
                fields={
                    'keyword': NormalizedKeyword(),
                    'trigram': TrigramText(),
                },
            ),
            'name_trigram': TrigramText(),
        },
    )


def company_field():
    """Company field with id, name, trading_names and trigrams."""
    return Object(
        properties={
            'id': Keyword(),
            'name': Text(
                fields={
                    'trigram': TrigramText(),
                },
            ),
            'trading_names': Text(
                fields={
                    'trigram': TrigramText(),
                },
            ),
        },
    )


def country_field():
    """Country field with id, name and trigram."""
    return Object(
        properties={
            'id': Keyword(),
            'name': Text(
                fields={
                    'trigram': TrigramText(),
                },
            ),
        },
    )


def address_field(index_country=True):
    """Address field as nested object."""
    if index_country:
        nested_country_field = country_field()
    else:
        nested_country_field = Object(
            properties={
                'id': Keyword(index=False),
                'name': Text(index=False),
            },
        )

    return Object(
        properties={
            'line_1': Text(index=False),
            'line_2': Text(index=False),
            'town': Text(index=False),
            'county': Text(index=False),
            'postcode': Text(
                fields={
                    'trigram': TrigramText(),
                },
            ),
            'country': nested_country_field,
        },
    )


def company_field_with_copy_to_name_trigram(field):
    """Company field with copy to, deprecated in favour of company_field"""
    return Object(
        properties={
            'id': Keyword(),
            'name': NormalizedKeyword(copy_to=f'{field}.name_trigram'),
            'name_trigram': TrigramText(),
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
        'company_number': NormalizedKeyword(),
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
            'name': NormalizedKeyword(),
            'ancestors': ancestors,
        },
    )


def object_field(*fields):
    """This is a mapping that reflects how Elasticsearch auto-creates mappings for objects."""
    return Object(
        properties={field: TextWithKeyword() for field in fields},
    )
