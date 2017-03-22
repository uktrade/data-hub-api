import uuid

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.utils.timezone import now

from datahub.core import constants
from datahub.interaction.models import ServiceDelivery
from datahub.interaction.test import factories
from datahub.v2.repos.service_deliveries import ServiceDeliveryDatabaseRepo

pytestmark = pytest.mark.django_db


class ServiceDeliveriesRepoTestCase(TestCase):

    def test_get(self):
        service_offer = factories.ServiceOfferFactory()
        service_delivery = factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        result = ServiceDeliveryDatabaseRepo().get(service_delivery.pk)
        assert result['relationships']
        assert result['relationships']['company']['data']['type'] == 'Company'
        assert result['attributes']['date'] == service_delivery.date.isoformat()

    def test_get_does_not_exist(self):
        with pytest.raises(ObjectDoesNotExist) as e:
            ServiceDeliveryDatabaseRepo().get(uuid.uuid4())

    def test_insert(self):
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
                        'id': factories.CompanyFactory().pk
                    }
                },
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': factories.ContactFactory().pk
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
        result = ServiceDeliveryDatabaseRepo().upsert(data=data)
        assert isinstance(result, ServiceDelivery)
