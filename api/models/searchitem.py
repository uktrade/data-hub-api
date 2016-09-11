from api.serializers.searchitemserializer import SearchItemSerializer
from datahubapi import settings


class SearchItem(object):
    def __init__(self, source_id, result_source, result_type, title, alt_title=None,
                 address_1=None, address_2=None, address_town=None, address_county=None,
                 address_country=None, address_postcode=None,
                 alt_address_1=None, alt_address_2=None, alt_address_town=None,
                 alt_address_county=None, alt_address_country=None, alt_address_postcode=None,
                 company_number=None, incorporation_date=None):
        self.source_id = source_id
        self.result_source = result_source
        self.result_type = result_type
        self.title = title
        self.address_1 = address_1
        self.address_2 = address_2
        self.address_town = address_town
        self.address_county = address_county
        self.address_country = address_country
        self.address_postcode = address_postcode
        self.alt_address_1 = alt_address_1
        self.alt_address_2 = alt_address_2
        self.alt_address_town = alt_address_town
        self.alt_address_county = alt_address_county
        self.alt_address_country = alt_address_country
        self.alt_address_postcode = alt_address_postcode
        self.company_number = company_number
        self.incorporation_date = incorporation_date
        self.alt_title = alt_title

    def save(self):
        try:
            serializer = SearchItemSerializer(self)
            data = serializer.data
            settings.ES_CLIENT.create(index=self.Meta.es_index_name,
                                      doc_type=self.Meta.es_type_name,
                                      body=data,
                                      refresh=True)
        except Exception as inst:
            print(inst)

    class Meta:
        es_index_name = 'datahub'
        es_type_name = 'searchindex'
        es_mapping = {
            'properties': {
                'source_id': {'type': 'string', 'index': 'not_analyzed'},
                'result_source': {'type': 'string', 'index': 'no'},
                'result_type': {'type': 'string', 'index': 'not_analyzed'},
                'title': {'type': 'string', 'index': 'not_analyzed', "boost": 3.0},
                'address_1': {'type': 'string', 'index': 'not_analyzed'},
                'address_2': {'type': 'string', 'index': 'not_analyzed'},
                'address_town': {'type': 'string', 'index': 'no'},
                'address_county': {'type': 'string', 'index': 'no'},
                'address_country': {'type': 'string', 'index': 'no'},
                'address_postcode': {'type': 'string', 'index': 'not_analyzed', "boost": 2.0},
                'alt_address_1': {'type': 'string', 'index': 'not_analyzed'},
                'alt_address_2': {'type': 'string', 'index': 'not_analyzed'},
                'alt_address_town': {'type': 'string', 'index': 'no'},
                'alt_address_county': {'type': 'string', 'index': 'no'},
                'alt_address_country': {'type': 'string', 'index': 'no'},
                'alt_address_postcode': {'type': 'string', 'index': 'not_analyzed', "boost": 2.0},
                'company_number': {'type': 'string', 'index': 'not_analyzed', "boost": 3.0},
                'incorporation_date': {'type': 'date', 'index': 'no'},
                'alt_title': {'type': 'string', 'index': 'not_analyzed', "boost": 3.0},
            }
        }
