from django.test import TestCase
from .serializers import CHCompanySerializer, SearchItemSerializer
from api.models import CHCompany, SearchItem
import json, requests


class SearchIndexSerializerTests(TestCase):

    def x_serialiser(self):
        search_index = SearchItem(
            source_id="123",
            source_type="COMPANY",
            title="My great company",
            summary="something that is shown in the search results",
            postcode="SL4 4QR")

        serializer = SearchItemSerializer(search_index)
        print(serializer.data)

    def test_search(self):
        data = {
            "query": {
                "query_string": {"query": "breathe"}
            }
        }
        response = requests.post('http://127.0.0.1:9200/datahub/_search', data=json.dumps(data))
        print(response.json())
