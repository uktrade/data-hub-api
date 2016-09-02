import gc
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk

from datahubapi import settings
from api.models.chcompany import CHCompany
from api.models.searchitem import SearchItem
from api.serializers import SearchItemSerializer


def create_index_item(ch: CHCompany, action="create"):

    search_item = SearchItem(
        source_id=ch.company_number,
        result_source="CH",
        result_type="COMPANY",
        title=ch.company_name,
        address_1=ch.registered_address_address_1,
        address_2=ch.registered_address_address_2,
        address_town=ch.registered_address_town,
        address_county=ch.registered_address_county,
        address_country=ch.registered_address_country,
        address_postcode=ch.registered_address_postcode,
        company_number=ch.company_number,
        incorporation_date=ch.incorporation_date
    )

    serializer = SearchItemSerializer(search_item)
    data = serializer.data
    metadata = {
        '_op_type': action,
        "_index": search_item.Meta.es_index_name,
        "_type": search_item.Meta.es_type_name,
    }
    data.update(**metadata)
    return data


def dump_buffer(buffer):
    print("Saving")
    bulk(
        client=settings.ES_CLIENT,
        actions=buffer,
        stats_only=True,
        chunk_size=1000,
        request_timeout=300)
    print("Saved")


def index_ch():
    buffer = []
    count = 0
    max_buffer = 10000

    paginator = Paginator(CHCompany.objects.all(), max_buffer)

    for page in range(1, paginator.num_pages + 1):
        for ch in paginator.page(page).object_list:
            buffer.append(create_index_item(ch=ch, action='create'))
            print("{0}, {1!s} - {2!s}".format(count, ch.company_number, ch.company_name))
            count += 1

            if count % max_buffer == 0:
                dump_buffer(buffer=buffer)
                buffer = []
                gc.collect()

        gc.collect()

    print("Almost done")
    dump_buffer(buffer=buffer)
    print("Done")


def recreate_index():
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


class Command(BaseCommand):

    help = 'Recreate CH Index'

    def handle(self, *args, **options):
        recreate_index()
        index_ch()
