import json
from unittest import mock

from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase

from datahub.interaction.test.factories import ServiceDeliveryFactory, ServiceOfferFactory
from datahub.interaction.models import ServiceDelivery


class ServiceDeliveryTestCase(LeelooTestCase):
    """Service Delivery test case."""

    def test_service_delivery_detail_view(self):
        """Service Delivery detail view."""
        service_offer = ServiceOfferFactory()
        servicedelivery = ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        url = reverse('v2:servicedelivery-detail', kwargs={'object_id': servicedelivery.pk})
        response = self.api_client.get(url)
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
        assert set(content.keys()) == {'data'}
        assert set(content['data'].keys()) == {'type', 'id', 'attributes', 'relationships', 'links'}
        assert content['data']['links']['self']

    def test_service_delivery_list_view(self):
        """Service delivery liste view."""
        service_offer = ServiceOfferFactory()
        service_deliveries = [
            ServiceDeliveryFactory(
                service=service_offer.service,
                dit_team=service_offer.dit_team)
            for i in range(6)]
        url = reverse('v2:servicedelivery-list')
        response = self.api_client.get(url)
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
        assert set(content.keys()) == {'links', 'data', 'meta'}
        assert set(content['links'].keys()) == {'first', 'last', 'next', 'prev'}
        assert set(content['meta'].keys()) == {'pagination'}
        assert set(content['meta']['pagination'].keys()) == {'count', 'limit', 'offset'}

    def test_add_service_delivery_incorrect_format(self):
        """Test add new service delivery with incorrect format."""
        service_offer = ServiceOfferFactory()
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
                        'type': 'foobar',
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
                        'id': service_offer.service.id
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': service_offer.dit_team.id
                    }
                }
            }
        }
        response = self.api_client.post(
            url,
            data=json.dumps({'data': data}),
            content_type='application/vnd.api+json'
        )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_service_delivery(self, mocked_save_to_korben):
        """Test add new service delivery."""
        service_offer = ServiceOfferFactory()
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
                        'id': service_offer.service.id
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': service_offer.dit_team.id
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
        service_offer = ServiceOfferFactory()
        servicedelivery = ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            event=service_offer.event,
            subject='I am a subject'
        )

        url = reverse('v2:servicedelivery-detail', kwargs={'object_id': servicedelivery.pk})
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

    def test_filter_service_deliveries_by_company(self):
        """Filter by company."""
        company = CompanyFactory()
        service_offer = ServiceOfferFactory()
        servicedelivery = ServiceDeliveryFactory(
            company=company,
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        servicedelivery2 = ServiceDeliveryFactory(
            company=company,
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        url = reverse('v2:servicedelivery-list')
        response = self.api_client.get(url, data={'company': company.pk})
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
        assert content['meta']['pagination']['count'] == 2
        assert {element['id'] for element in content['data']} == {str(servicedelivery.pk), str(servicedelivery2.pk)}

    def test_filter_service_deliveries_by_contact(self):
        """Filter by contact."""
        contact = ContactFactory()
        service_offer = ServiceOfferFactory()
        servicedelivery = ServiceDeliveryFactory(
            contact=contact,
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        servicedelivery2 = ServiceDeliveryFactory(
            contact=contact,
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        url = reverse('v2:servicedelivery-list')
        response = self.api_client.get(url, data={'contact': contact.pk})
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
        assert content['meta']['pagination']['count'] == 2
        assert {element['id'] for element in content['data']} == {str(servicedelivery.pk), str(servicedelivery2.pk)}

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_service_delivery_incorrect_service_team_event_combination(self, mocked_save_to_korben):
        """Test add new service delivery with invalid service/team/even combination."""
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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        content = {
            'errors': [{
                'detail': 'This combination of service and service provider does not exist.',
                'source': {'pointer': '/data/attributes/service'},
                'status': '400'}
            ]}
        assert json.loads(response.content.decode('utf-8')) == content
        assert not mocked_save_to_korben.delay.called
