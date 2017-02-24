import json
from unittest import mock

from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase

from .factories import ServiceDeliveryFactory
from ..models import ServiceDelivery


class ServiceDeliveryTestCase(LeelooTestCase):
    """Service Delivery test case."""

    def test_service_delivery_detail_view(self):
        """Service Delivery detail view."""
        servicedelivery = ServiceDeliveryFactory()
        url = reverse('v2:servicedelivery-detail', kwargs={'pk': servicedelivery.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(servicedelivery.pk)

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_service_delivery(self, mocked_save_to_korben):
        """Test add new service delivery."""
        url = reverse('v2:servicedelivery-list')
        data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'subject': 'whatever',
                'date': now().isoformat(),
                'notes': 'hello',
            },
            'relationships': {
                'status': {
                    'data': {
                        'type': 'ServiceDeliveryStatus',
                        'id': constants.ServiceDeliveryStatus.offered.value.id
                    }
                },
                'company': {
                    'data': {
                        'type': 'Company',
                        'id': CompanyFactory().pk
                    }
                },
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': ContactFactory().pk
                    }
                },
                'service': {
                    'data': {
                        'type': 'Service',
                        'id': constants.Service.trade_enquiry.value.id
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': constants.Team.healthcare_uk.value.id
                    }
                }
            }
        }
        response = self.api_client.post(
            url,
            data=json.dumps({'data': data}),
            content_type='application/vnd.api+json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        # make sure we're spawning a task to save to Korben
        expected_data = ServiceDelivery.objects.get(pk=response.data['id']).convert_model_to_korben_format()
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='interaction_servicedelivery',
            data=expected_data,
            update=False,
            user_id=self.user.id
        )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_service_delivery_incorrect_accept_header_format(self, mocked_save_to_korben):
        """Test add new service delivery incorrect accept header format."""
        url = reverse('v2:servicedelivery-list')
        data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'subject': 'whatever',
                'date': now().isoformat(),
                'notes': 'hello',
            },
            'relationships': {
                'status': {
                    'data': {
                        'type': 'ServiceDeliveryStatus',
                        'id': constants.ServiceDeliveryStatus.offered.value.id
                    }
                },
                'company': {
                    'data': {
                        'type': 'Company',
                        'id': CompanyFactory().pk
                    }
                },
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': ContactFactory().pk
                    }
                },
                'service': {
                    'data': {
                        'type': 'Service',
                        'id': constants.Service.trade_enquiry.value.id
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': constants.Team.healthcare_uk.value.id
                    }
                }
            }
        }
        response = self.api_client.post(
            url,
            data=json.dumps({'data': data}),
            content_type='application/vnd.api+json',
            **{'HTTP_ACCEPT': 'application/json'}
        )
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        expected_content = b'{"errors":{"detail":"Could not satisfy the request Accept header."}}'
        assert response.content == expected_content
        # make sure we're not spawning a task to save to Korben
        assert mocked_save_to_korben.delay.called is False

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    @freeze_time('2017-01-27 12:00:01')
    def test_modify_service_delivery(self, mocked_save_to_korben):
        """Modify an existing service delivery."""
        servicedelivery = ServiceDeliveryFactory(subject='I am a subject')

        url = reverse('v2:servicedelivery-detail', kwargs={'pk': servicedelivery.pk})
        response = self.api_client.patch(url, {
            'subject': 'I am another subject',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'
        # make sure we're spawning a task to save to Korben
        expected_data = servicedelivery.convert_model_to_korben_format()
        expected_data['subject'] = 'I am another subject'
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='interaction_servicedelivery',
            data=expected_data,
            update=True,
            user_id=self.user.id
        )
