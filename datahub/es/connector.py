from django.conf import settings
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q, Term

from .utils import document_exists, get_elasticsearch_client


class ESConnector:
    """Elastichsearch connector."""

    def __init__(self):
        """Initialise client and search class."""
        self.client = get_elasticsearch_client()
        self.search = Search(using=self.client, index=settings.ES_INDEX)

    def search_by_term(self, term, doc_type=None, offset=0, limit=100):
        """Perform a multi match search query."""
        if doc_type:
            if isinstance(doc_type, str):
                doc_type = [doc_type]

            q = self.search.query(Q('terms', _type=doc_type)).filter(
                'multi_match', query=term, fields=['name^3', 'alias^3', '*_name', '*_postcode']
            )
        else:
            q = self.search.query(Q(
                'multi_match', query=term, fields=['name^3', 'alias^3', '*_name', '*_postcode']
            ))

        return q[offset:offset + limit].execute()
