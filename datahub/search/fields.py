from functools import partial

from opensearch_dsl import Date, Keyword, Object, Text

from datahub.search.opensearch import (
    lowercase_asciifolding_normalizer,
    postcode_analyzer,
    postcode_search_analyzer,
)

# Keyword with normalisation to improve sorting (by keeping e, E, è, ê etc. together).
NormalizedKeyword = partial(
    Keyword,
    normalizer=lowercase_asciifolding_normalizer,
)
TrigramText = partial(Text, analyzer='trigram_analyzer')
EnglishText = partial(Text, analyzer='english_analyzer')
TextWithTrigram = partial(
    Text,
    fields={
        'trigram': TrigramText(),
    },
)
# Keyword with normalisation that recognises UK postcodes to improve searching
PostcodeKeyword = partial(
    Text,
    analyzer=postcode_analyzer,
    search_analyzer=postcode_search_analyzer,
)


def contact_or_adviser_field(include_dit_team=False):
    """Object field for advisers and contacts."""
    props = {
        'id': Keyword(),
        'first_name': NormalizedKeyword(),
        'last_name': NormalizedKeyword(),
        'name': Text(
            fields={
                'keyword': NormalizedKeyword(),
                'trigram': TrigramText(),
            },
        ),
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


def id_name_partial_field():
    """Object field with id and name sub-fields, and with partial matching on name."""
    return Object(
        properties={
            'id': Keyword(),
            'name': Text(
                fields={
                    'keyword': NormalizedKeyword(),
                    'trigram': TrigramText(),
                },
            ),
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
                    'keyword': NormalizedKeyword(),
                },
            ),
            'trading_names': TextWithTrigram(),
        },
    )


def country_field():
    """Country field with id, name and trigram."""
    return Object(
        properties={
            'id': Keyword(),
            'name': TextWithTrigram(),
        },
    )


def area_field():
    """Area field with id, name and trigram."""
    return Object(
        properties={
            'id': Keyword(),
            'name': TextWithTrigram(),
        },
    )


def address_field():
    """Address field as nested object."""
    return Object(
        properties={
            'line_1': TextWithTrigram(),
            'line_2': TextWithTrigram(),
            'town': TextWithTrigram(),
            'county': TextWithTrigram(),
            'area': area_field(),
            'postcode': TextWithTrigram(),
            'country': country_field(),
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


def interaction_field():
    """Interaction field with id, subject and date."""
    return Object(
        properties={
            'id': Keyword(),
            'subject': Text(index=False),
            'date': Date(),
        },
    )
