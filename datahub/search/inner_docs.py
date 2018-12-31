from elasticsearch_dsl import InnerDoc, Keyword, Text


class UnindexedInnerIDName(InnerDoc):
    """InnerDoc for an unsearchable ID and name object."""

    id = Keyword(index=False)
    name = Text(index=False)
