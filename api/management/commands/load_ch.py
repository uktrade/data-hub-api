import csv
import datetime
import gc
from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from api.models.searchitem import SearchItem
from api.models.chcompany import CHCompany
from api.serializers import SearchItemSerializer

DATE_FIELDS = (
    'incorporation_date',
)

FIELDS = (
    'company_number',
    'company_name',
    'registered_address_care_of',
    'registered_address_po_box',
    'registered_address_address_1',
    'registered_address_address_2',
    'registered_address_town',
    'registered_address_county',
    'registered_address_country',
    'registered_address_postcode',
    'company_category',
    'company_status',
    'sic_code_1',
    'sic_code_2',
    'sic_code_3',
    'sic_code_4',
    'uri',
    'incorporation_date',
)


def create_company(row):
    data = {}

    for key in FIELDS:
        if len(row[key]) == 0:
            row[key] = None

        if row[key] is not None and key in DATE_FIELDS or row[key] is not None and 'date' in key:
            row_value = row[key]
            if row_value is not None:
                day, month, year = row_value.split('/')
                data[key] = "{0}-{1}-{2}".format(year, month, day)
        else:
            data[key] = row[key]

    company = CHCompany(**data)

    return company


def create_index_item(row, action='create'):

    if row['incorporation_date'] is not None:
        day, month, year = row['incorporation_date'].split('/')
        incorporation_date = datetime.date(int(year), int(month), int(day))
    else:
        incorporation_date = None

    search_item = SearchItem(
        source_id=row['company_number'],
        result_source="CH",
        result_type="COMPANY",
        title=row['company_name'],
        address_1=row['registered_address_address_1'],
        address_2=row['registered_address_address_2'],
        address_town=row['registered_address_town'],
        address_county=row['registered_address_county'],
        address_country=row['registered_address_country'],
        address_postcode=row['registered_address_postcode'],
        company_number=row['company_number'],
        incorporation_date=incorporation_date
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


def create_index():
    indices_client = IndicesClient(client=settings.ES_CLIENT)
    index_name = SearchItem.Meta.es_index_name

    if not indices_client.exists(index_name):
        indices_client.create(index=index_name)

        indices_client.put_mapping(
            doc_type=SearchItem.Meta.es_type_name,
            body=SearchItem.Meta.es_mapping,
            index=index_name
        )


def dump_buffers(ch_buffer, index_buffer):
    # save db objects
    CHCompany.objects.bulk_create(ch_buffer)
    # save search index items
    bulk(
        client=settings.ES_CLIENT,
        actions=index_buffer,
        stats_only=True,
        chunk_size=1000,
        request_timeout=300)


class Command(BaseCommand):
    help = 'Load Companies House CSV'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, filename, *args, **options):

        print("Creating Index in elastic search")
        create_index()

        count = 0
        max_buffer = 5000
        ch_buffer = []
        index_buffer = []

        # Open the csv file and parse as a collection of dictionaries
        with open(filename, 'r') as csv_fh:
            rows = csv.DictReader(csv_fh)

            # Iterate through reach row and build a new company record in a buffer
            for row in rows:
                if CHCompany.objects.filter(company_number=row['company_number']).exists():
                    print("{0!s} already exists".format(row['company_number']))
                else:
                    ch_buffer.append(create_company(row))
                    index_buffer.append(create_index_item(row, 'create'))
                    count += 1

                    print("{0}, {1!s} - {2!s}".format(count, row['company_number'], row['company_name']))

                    if count % max_buffer == 0:
                        dump_buffers(ch_buffer=ch_buffer, index_buffer=index_buffer)
                        ch_buffer = []
                        index_buffer = []
                        gc.collect()

        print("Finished, saving remaining records.")
        dump_buffers(ch_buffer=ch_buffer, index_buffer=index_buffer)
