import json

from rest_framework.reverse import reverse

from datahub.core.test_utils import LeelooTestCase


class JSONParserTestCase(LeelooTestCase):
    """Test generic parser error through a v2 view."""

    def test_data_key_not_in_post_body(self):
        """Test data key is missing from post body."""
        url = reverse('v2:servicedelivery-list')
        data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'subject': 'whatever',
                'date': 'foo',
                'notes': 'hello',
            },
            'relationships': {
                'status': {
                    'data': {
                        'type': 'foobar',
                        'id': 'bar'
                    }
                },
            }
        }
        response = self.api_client.post(
            url,
            data=json.dumps(data),
            content_type='application/vnd.api+json'
        )
        content = json.loads(response.content.decode('utf-8'))
        expected_content = {'errors': [
            {'source': {'pointer': '/data/detail'},
             'detail': 'Received document does not contain primary data.'}]
        }
        assert content == expected_content

    def test_data_contains_incorrect_entity_name(self):
        """Test add new service delivery with incorrect format."""
        url = reverse('v2:servicedelivery-list')
        data = {
            'type': 'whatever',
            'attributes': {
                'subject': 'whatever',
                'date': 'foo',
                'notes': 'hello',
            },
            'relationships': {
                'status': {
                    'data': {
                        'type': 'foobar',
                        'id': 'bar'
                    }
                },
            }
        }
        response = self.api_client.post(
            url,
            data=json.dumps({'data': data}),
            content_type='application/vnd.api+json'
        )
        content = json.loads(response.content.decode('utf-8'))
        expected_content = {'errors': [
            {'detail': 'The resource object\'s type (whatever) is not the type that constitute the collection '
                       'represented by the endpoint (ServiceDelivery).',
             'source': {'pointer': '/data/detail'}
             }]
        }
        assert content == expected_content
