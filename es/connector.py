from django.conf import settings
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Term

from es.services import document_exists
from es.utils import get_elasticsearch_client


class ESConnector:

    def __init__(self):
        self.client = get_elasticsearch_client()
        self.search = Search(using=self.client, index=settings.ES_INDEX)

    def save(self, doc_type, data):
        """Add or update data to ES."""

        if doc_type == 'company_company' and data['company_number']:
            self.handle_ch_company(data)

        object_id = data.pop('id')  # take it out until we sort out the manual mapping
        if document_exists(self.client, doc_type, object_id):
            self.client.update(
                index=settings.ES_INDEX,
                doc_type=doc_type,
                body={'doc': data},
                id=object_id,
                refresh=True
            )
        else:
            self.client.create(
                index=settings.ES_INDEX,
                doc_type=doc_type,
                body=data,
                id=object_id,
                refresh=True
            )

    def handle_ch_company(self, data):
        """If trying to promote a company house to an internal company, delete che CH record."""

        query = Term(company_number=data['company_number'])
        search = self.search.doc_type('company_companieshousecompany').query(query)
        results = search.execute()
        if results:
            self.client.delete(
                index=settings.ES_INDEX,
                doc_type='company_companieshousecompany',
                id=results[0].meta.id,
                refresh=True
            )

    def search_by_term(self, term, doc_type=None, offset=0, limit=100):
        """Perform a query term search."""

        search_client = self.search.doc_type(*doc_type) if doc_type else self.search
        search = search_client.query(
            'query_string',
            query=term
        )[offset:offset + limit]
        results = search.execute()

        return results
