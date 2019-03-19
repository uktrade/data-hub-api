from elasticsearch_dsl import InnerDoc, Keyword, Text

from datahub.search.fields import TrigramText


class Person(InnerDoc):
    """Inner doc for a person (e.g. a contact or an adviser)."""

    id = Keyword()
    first_name = Text(index=False)
    last_name = Text(index=False)
    name = Text(
        fields={
            'trigram': TrigramText(),
        },
    )


class IDNameTrigram(InnerDoc):
    """Inner doc for a named object, with a trigram sub-field on name."""

    id = Keyword()
    name = Text(
        fields={
            'trigram': TrigramText(),
        },
    )
