from elasticsearch.client import IndicesClient
from django.conf import settings
from django.core.management.base import BaseCommand
from api.models.searchitem import SearchItem


class Command(BaseCommand):

    help = 'Drop Index'

    def handle(self, *args, **options):
        indices_client = IndicesClient(client=settings.ES_CLIENT)
        index_name = SearchItem.Meta.es_index_name

        if indices_client.exists(index_name):
            indices_client.delete(index=index_name)

        indices_client.create(index=index_name)

        indices_client.put_mapping(
            doc_type=SearchItem.Meta.es_type_name,
            body=SearchItem.Meta.es_mapping,
            index=index_name
        )
