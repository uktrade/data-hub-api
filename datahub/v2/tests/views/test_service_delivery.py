import json

from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase

from datahub.interaction.test.factories import ServiceDeliveryFactory, ServiceOfferFactory


class ServiceDeliveryViewTestCase(LeelooTestCase):
    """Service Delivery view test case."""

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
        assert content.keys() == {'data'}
        assert content['data'].keys() == {'type', 'id', 'attributes', 'relationships', 'links'}
        assert content['data']['links']['self']

    def test_service_delivery_list_view(self):
        """Service delivery liste view."""
        service_offer = ServiceOfferFactory()
        [
            ServiceDeliveryFactory(
                service=service_offer.service,
                dit_team=service_offer.dit_team)
            for i in range(6)]
        url = reverse('v2:servicedelivery-list')
        response = self.api_client.get(url)
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
        assert content.keys() == {'links', 'data', 'meta'}
        assert content['links'].keys() == {'first', 'last', 'next', 'prev'}
        assert content['meta'].keys() == {'pagination'}
        assert content['meta']['pagination'].keys() == {'count', 'limit', 'offset'}

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
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        expected_content = {'errors': [{
            'detail': 'type foobar should be ServiceDeliveryStatus',
            'source': {'pointer': '/data/relationships/status'}
        }]}
        assert content == expected_content

    def test_add_service_delivery(self):
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

    def test_add_service_delivery_incorrect_accept_header_format(self):
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
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        expected_content = {'errors': [{
            'detail': 'Could not satisfy the request Accept header.',
            'source': {'pointer': '/data/detail'}
        }]}
        assert content == expected_content

    def test_modify_service_delivery(self):
        """Modify an existing service delivery."""
        service_offer = ServiceOfferFactory()
        servicedelivery = ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            event=service_offer.event,
            subject='I am a subject',
            uk_region_id=constants.UKRegion.east_midlands.value.id
        )

        url = reverse('v2:servicedelivery-list')
        data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'subject': 'I am another subject',
            },
            'relationships': {
                'uk_region': {
                    'data': None
                }
            },
            'id': str(servicedelivery.pk)
        }
        response = self.api_client.post(
            url,
            data=json.dumps({'data': data}),
            content_type='application/vnd.api+json'
        )

        assert response.status_code == status.HTTP_200_OK
        content = json.loads(response.content.decode('utf-8'))
        assert content['data']['attributes']['subject'] == 'I am another subject'
        assert 'uk_region' not in content['data']['relationships'].keys()

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
        response = self.api_client.get(url, data={'company_id': company.pk})
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
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
        response = self.api_client.get(url, data={'contact_id': contact.pk})
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status.HTTP_200_OK
        assert {element['id'] for element in content['data']} == {str(servicedelivery.pk), str(servicedelivery2.pk)}

    def test_add_service_delivery_incorrect_service_team_event_combination(self):
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
                'source': {'pointer': '/data/relationships/service'}
            }]}
        assert json.loads(response.content.decode('utf-8')) == content
