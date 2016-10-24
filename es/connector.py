from django.conf import settings

from es.services import document_exists
from es.utils import get_elasticsearch_client


class ESConnector:

    def __init__(self):
        self.client = get_elasticsearch_client()

    def save(self, doc_type, data):
        """Add or update data to ES."""

        if doc_type == 'company_company':
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

        if document_exists(self.client, 'company_companieshousecompany', data['id']):
            self.client.delete(
                index=settings.ES_INDEX,
                doc_type='company_companieshousecompany',
                id=data['id'],
                refresh=True
            )
